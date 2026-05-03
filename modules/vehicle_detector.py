# ═══════════════════════════════════════════════════════════════════════════════
#  modules/vehicle_detector.py
#  Days 8 (class), 9 (ByteTrack), 10 (counting line) — COMPLETE
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, os, sys, numpy as np
from collections import defaultdict, deque
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    VEHICLE_MODEL, FALLBACK_MODEL,
    CONFIDENCE_THRESHOLD, TWO_WHEELER_IDS, TWO_WHEELER_LABELS,
    SKIP_FRAMES, SHOW_TRACK_IDS, SHOW_CONFIDENCE,
    SHOW_TRAILS, SHOW_COUNT_LINE, COUNT_LINE_POSITION, TRAIL_LENGTH,
    USING_CUSTOM_VEHICLE_MODEL,
)
from utils.helpers import put_stats_overlay

# Colours work for both custom model (class 0) and COCO (classes 1, 3)
_PALETTE = [(255, 165, 0), (0, 120, 255), (0, 200, 220)]
VEHICLE_COLORS = {cid: _PALETTE[i % len(_PALETTE)]
                  for i, cid in enumerate(TWO_WHEELER_IDS)}
COLOR_COUNTED  = (0, 220, 0)


class VehicleDetector:
    """
    Day 8: Class architecture, standard detection dict, frame skipping
    Day 9: ByteTrack IDs, track_types, trail_history, ID badges
    Day 10: counted_ids set, counting line, live total, flash on crossing
    """

    def __init__(self, model_path=None):
        from ultralytics import YOLO
        path = model_path or VEHICLE_MODEL
        if not os.path.exists(path):
            print(f"[VehicleDetector] {path} not found → using {FALLBACK_MODEL}")
            path = FALLBACK_MODEL
        self.model      = YOLO(path)
        self.model_path = path
        src = "custom vehicle_detector.pt" if USING_CUSTOM_VEHICLE_MODEL else "COCO fallback"
        print(f"[VehicleDetector] Mode: {src}  |  classes: {TWO_WHEELER_LABELS}")

        # Day 8: frame skipping
        self._skip    = SKIP_FRAMES
        self._frame_n = 0
        self._cache   = []

        # Day 9: tracking
        self.track_types   = {}
        self.trail_history = defaultdict(lambda: deque(maxlen=TRAIL_LENGTH))

        # Day 10: counting
        self.counted_ids = set()
        self.line_y      = None

        print(f"[VehicleDetector] Loaded: {path}")

    # ── PUBLIC API ────────────────────────────────────────────────────────────
    def process_frame(self, frame, frame_num=None):
        if frame_num is not None: self._frame_n = frame_num
        else: self._frame_n += 1

        h = frame.shape[0]
        if self.line_y is None:
            self.line_y = int(h * COUNT_LINE_POSITION)

        # Day 8: frame skip
        if self._skip > 1 and self._frame_n % self._skip != 0:
            newly = self._check_counting(self._cache)
            return {'detections':self._cache,'total_counted':len(self.counted_ids),
                    'newly_counted':newly,'line_y':self.line_y,'frame_num':self._frame_n}

        self._cache       = self._detect(frame)
        newly_counted     = self._check_counting(self._cache)
        return {'detections':self._cache,'total_counted':len(self.counted_ids),
                'newly_counted':newly_counted,'line_y':self.line_y,'frame_num':self._frame_n}

    def draw(self, frame, result):
        self._draw_counting_line(frame, result)
        for det in result['detections']:
            self._draw_single(frame, det)
        self._draw_stats_panel(frame, result)

    def draw_trails(self, frame):
        if not SHOW_TRAILS: return
        for tid, pts in self.trail_history.items():
            pts = list(pts)
            if len(pts) < 2: continue
            vtype  = self.track_types.get(tid, '')
            # resolve class id for this track (works for both custom and COCO)
            cls_id = next(
                (cid for cid, lbl in TWO_WHEELER_LABELS.items() if lbl in vtype),
                TWO_WHEELER_IDS[0]
            )
            color  = VEHICLE_COLORS.get(cls_id, (180, 180, 180))
            for i in range(1,len(pts)):
                a = i/len(pts)
                cv2.line(frame,pts[i-1],pts[i],tuple(int(c*a) for c in color),max(1,int(a*3)))
            if pts: cv2.circle(frame,pts[-1],4,color,-1)

    def reset(self):
        self._frame_n=0; self._cache=[]; self.track_types={}
        self.trail_history.clear(); self.counted_ids.clear(); self.line_y=None
        print("[VehicleDetector] Reset")

    # ── PRIVATE ───────────────────────────────────────────────────────────────
    def _detect(self, frame):
        # Day 9: model.track with persist=True
        results = self.model.track(frame, persist=True,
                                   conf=CONFIDENCE_THRESHOLD,
                                   classes=list(TWO_WHEELER_IDS),
                                   verbose=False)
        dets = []
        r = results[0]
        if r.boxes is None or len(r.boxes)==0: return dets
        for box in r.boxes:
            x1,y1,x2,y2 = map(int,box.xyxy[0].tolist())
            cls_id = int(box.cls[0]);  conf = float(box.conf[0])
            cx=(x1+x2)//2;            cy=(y1+y2)//2
            vtype = TWO_WHEELER_LABELS.get(cls_id,'vehicle')
            # Day 9: safe track_id extraction
            track_id = int(box.id[0]) if box.id is not None else None
            if track_id is not None:
                self.track_types[track_id] = vtype
                self.trail_history[track_id].append((cx,cy))
            dets.append({
                'track_id':track_id,'vehicle_type':vtype,'cls_id':cls_id,
                'conf':conf,'box':[x1,y1,x2,y2],'cx':cx,'cy':cy,
                'counted':(track_id in self.counted_ids) if track_id else False,
                'rider_count':None,'rider_label':None,
                'helmet_status':None,'plate':None,
            })
        return dets

    def _check_counting(self, detections):
        # Day 10: counting line logic
        if self.line_y is None: return []
        newly = []
        for det in detections:
            tid = det['track_id']
            if tid is None: continue
            if det['cy'] > self.line_y and tid not in self.counted_ids:
                self.counted_ids.add(tid)
                det['counted'] = True
                newly.append(tid)
        return newly

    def _draw_single(self, frame, det):
        x1,y1,x2,y2 = det['box']
        counted      = det['counted']
        color        = COLOR_COUNTED if counted else VEHICLE_COLORS.get(det['cls_id'],(180,180,180))
        thick        = 3 if counted else 2
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,thick)
        if counted:
            cv2.rectangle(frame,(x1-2,y1-2),(x2+2,y2+2),COLOR_COUNTED,1)
        parts=[]
        tid=det['track_id']
        if tid is not None and SHOW_TRACK_IDS: parts.append(f"ID:{tid}")
        parts.append(det['vehicle_type'])
        if SHOW_CONFIDENCE: parts.append(f"{det['conf']:.2f}")
        label=(" ".join(parts))
        (tw,th),bl=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.52,2)
        ly = y1 if y1>th+10 else y2+th+10
        cv2.rectangle(frame,(x1,ly-th-bl-4),(x1+tw+4,ly),color,-1)
        cv2.putText(frame,label,(x1+2,ly-bl-1),cv2.FONT_HERSHEY_SIMPLEX,0.52,(255,255,255),2)
        if tid is not None:
            bx,by=x2-14,y1+14
            cv2.circle(frame,(bx,by),13,color,-1)
            cv2.circle(frame,(bx,by),13,(255,255,255),1)
            ids=str(tid); (tw2,_),_=cv2.getTextSize(ids,cv2.FONT_HERSHEY_SIMPLEX,0.45,1)
            cv2.putText(frame,ids,(bx-tw2//2,by+4),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,255,255),1)

    def _draw_counting_line(self, frame, result):
        if not SHOW_COUNT_LINE or self.line_y is None: return
        h,w = frame.shape[:2]
        newly = result.get('newly_counted',[])
        lc    = (0,220,255) if newly else (0,0,255)
        # Dashed line
        x=0
        while x<w:
            cv2.line(frame,(x,self.line_y),(min(x+25,w),self.line_y),lc,2)
            x+=37
        cv2.putText(frame,"COUNT LINE",(10,self.line_y-6),
                    cv2.FONT_HERSHEY_SIMPLEX,0.55,lc,2)
        # Total badge
        total=result.get('total_counted',0)
        txt=f"TOTAL: {total}"
        (btw,bth),_=cv2.getTextSize(txt,cv2.FONT_HERSHEY_SIMPLEX,1.0,2)
        bx1=w-btw-24; bx2=w-10; by1=10; by2=10+bth+20
        ov=frame.copy()
        cv2.rectangle(ov,(bx1,by1),(bx2,by2),(0,0,0),-1)
        cv2.addWeighted(ov,0.6,frame,0.4,0,frame)
        cv2.rectangle(frame,(bx1,by1),(bx2,by2),lc,2)
        cv2.putText(frame,txt,(bx1+10,by2-8),cv2.FONT_HERSHEY_SIMPLEX,1.0,(255,255,255),2)
        if newly:
            cv2.putText(frame,f"+{len(newly)} NEW",(bx1+10,by2+28),
                        cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,255),2)

    def _draw_stats_panel(self, frame, result):
        dets  = result['detections']
        stats = {
            'Frame':    result.get('frame_num', 0),
            'In frame': len(dets),
            'Counted':  result.get('total_counted', 0),
        }
        # Per-class counts — works for custom (0:two-wheeler) and COCO (1,3)
        for cid, lbl in TWO_WHEELER_LABELS.items():
            stats[lbl.capitalize()] = sum(1 for d in dets if d['cls_id'] == cid)
        put_stats_overlay(frame, stats)

