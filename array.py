import cv2
import numpy as np 

img = np.zeros((200, 400, 3), dtype=np.uint8)
print(img.shape)
print(img.dtype)
print(img.max())


pixel=img[100, 200]
print(pixel)

img[100, 200] = [0, 0, 255]

img[10:80, 50:150] = [0, 255, 0]
img[120:180, 250:350] = [255, 100, 0]

cv2.imshow("Pixel manipulation (press any key)", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

