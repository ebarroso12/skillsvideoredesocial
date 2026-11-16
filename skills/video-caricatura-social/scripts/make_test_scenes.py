#!/usr/bin/env python3
"""Gera cenas sinteticas (NAO sao arte final) so para testar o motor de video. Uso: make_test_scenes.py PASTA_DE_SAIDA"""
import sys, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
random.seed(7)
PALETAS = [((250,200,120),(60,90,160)), ((30,40,90),(200,120,140)), ((255,230,190),(90,150,120)),
           ((20,30,60),(240,200,90)), ((235,225,255),(120,100,190))]
def grad(w,h,a,b):
    im = Image.new("RGB",(w,h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t=y/h; d.line([(0,y),(w,y)],fill=tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3)))
    return im
def figure(d,cx,cy,s):
    d.ellipse([cx-s*0.9,cy-s*1.7,cx+s*0.9,cy-s*0.0],fill=(236,190,150),outline=(60,40,30),width=6)   # cabeca grande (caricatura)
    d.ellipse([cx-s*0.45,cy-s*1.05,cx-s*0.15,cy-s*0.8],fill=(255,255,255),outline=(0,0,0),width=4)
    d.ellipse([cx+s*0.15,cy-s*1.05,cx+s*0.45,cy-s*0.8],fill=(255,255,255),outline=(0,0,0),width=4)
    d.arc([cx-s*0.4,cy-s*0.6,cx+s*0.4,cy-s*0.2],20,160,fill=(120,40,40),width=8)
    d.rectangle([cx-s*0.6,cy,cx+s*0.6,cy+s*1.6],fill=(30,60,110),outline=(10,20,40),width=6)
for i,(a,b) in enumerate(PALETAS,1):
    sq = (i==3)                      # cena 3 quadrada -> testa fundo desfocado
    w,h = (1080,1080) if sq else (1080,1920)
    im = grad(w,h,a,b); d = ImageDraw.Draw(im)
    for _ in range(14):
        x,y,r = random.randint(0,w),random.randint(0,h//2),random.randint(60,200)
        d.ellipse([x-r,y-r*0.5,x+r,y+r*0.5],fill=(255,255,255))
    im = im.filter(ImageFilter.GaussianBlur(6)); d = ImageDraw.Draw(im)
    figure(d,w//2,int(h*0.62),w*0.16)
    im.save(out/f"cena_{i:02d}.png")
print("ok", out)
