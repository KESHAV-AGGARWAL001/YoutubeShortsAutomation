@echo off
echo Testing FFmpeg text rendering...
ffmpeg -y -f lavfi -i "color=c=black:size=1920x1080:duration=3:rate=30" -vf "drawtext=text='Test Text':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2:shadowcolor=black:shadowx=2:shadowy=2" -c:v libx264 -preset ultrafast -t 3 output\test_clip.mp4
echo.
if exist output\test_clip.mp4 (
    echo SUCCESS - FFmpeg text rendering works!
    echo Open output\test_clip.mp4 to verify
) else (
    echo FAILED - Check error above
)
pause
