# HOME CITY 50s 3D ad (9:16)

Uses the real product photos from the website zip (cut out into `img/`).

Render (from this folder, needs `node_modules` with three + @fontsource, same as gyaan-factory):
```bash
ln -s ../gyaan-factory/node_modules node_modules
for i in 0 1 2 3; do DSF=2 node render.js video $((i*375)) $(((i+1)*375)) seg$i.mp4 & done; wait
printf "file seg%d.mp4\n" 0 1 2 3 > l.txt
ffmpeg -f concat -i l.txt -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest HOME_CITY_Ad_1080x1920.mp4
```
