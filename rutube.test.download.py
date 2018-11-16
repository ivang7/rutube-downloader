import requests
from pathlib import Path

import re
import json
import m3u8


def videoDownload(params):
    urlVideo = params[0]
    indexOfVideo = params[1]
    
    print "{} - START download video".format(indexOfVideo)
    
    video =  requests.get(urlVideo)
    with open("./download/video" + str(indexOfVideo) + ".mp4", 'wb') as f:
        f.write(video.content)

    print "{} - FINISH download video".format(indexOfVideo)


VIDEO_URL = 'https://rutube.ru/video/8f35c1838c6eb8ad2068d9d6aae0a47e/'

######## get HTML with video, find id
video =  requests.get(VIDEO_URL)
if video.status_code == 200 :
    m = re.search(r'<meta property="og:video" content="http://rutube.ru/play/embed/(\d+)" />', video.content)
    videoId = m.group(1)
    print ('Get video, internal id = {}'.format(videoId))
else :
    print ('Error, cant get video, HTTP_CODE = {}'.format(video.status_code))

###### get video options by id (url variant playlist)
videoOptions = requests.get('https://rutube.ru/api/play/options/{}/?format=json'.format(videoId))
if videoOptions.status_code == 200 :
    videoOptionsJson = json.loads(videoOptions.content)
    playListUrl = videoOptionsJson['video_balancer']['m3u8']
    print ('Get options, playlist url = {}'.format(playListUrl))
else :
    print ('Error, cant get videoOptions, HTTP_CODE = {}'.format(videoOptions.status_code))

##### get variant playlist
playList = requests.get(playListUrl)
if playList.status_code == 200 :
    print (playList.content)
else :
    print ('Error, cant get playlist, HTTP_CODE = {}'.format(videoOptions.status_code))

##### parse m3u8 variant playlist, get maximum quality
variant_m3u8 = m3u8.loads(playList.content)
zz = [[playlist.stream_info.resolution,playlist.uri] for playlist in variant_m3u8.playlists]
zz.sort(reverse = True)
playListWithHighQualityVideo = zz[0][1]

##### save base url from playlist (need for generate video url)
#baseUrlForVideo = playListWithHighQualityVideo.rpartition('/')[0] + '/'
#print(baseUrlForVideo)

#### get playlist with all video
m3u8_obj = m3u8.load(playListWithHighQualityVideo)
baseUrlForVideo =  m3u8_obj.base_uri


segmentDuration =  m3u8_obj.target_duration
urls = [baseUrlForVideo + url for url  in m3u8_obj.files]
#videoDownload(urls[0], 0)
#exit()

advertMetaData = requests.get("https://rutube.ru/api/play/trackinfo/{}/?format=json&extended_cuepoints=true".format(videoId))
if advertMetaData.status_code == 200 :
    advertMetaDataJson = json.loads(advertMetaData.content)
    chapters = [{'advert':chapter['forbid_seek'], 'time':chapter['time']} for chapter in advertMetaDataJson['cuepoints']]
    print ('Get advert = {}'.format(chapters))
else :
    print ('Error, cant get advert meta data, HTTP_CODE = {}'.format(advertMetaData.status_code))

chapters = sorted(chapters,key=lambda chapter: chapter['time'])
i = 0
advert = False
while i < len (chapters) :
    if chapters[i]['advert'] == advert :
        del chapters[i]
    else:
        advert = chapters[i]['advert']
        chapters[i]['time'] /= 1000.0
        i += 1
print ('Get advert = {}'.format(chapters))

import pprint
pprint.pprint(chapters)

####### create arg for join wo advert
startTimePreviousChapter = 0.0
previousVideoIndex = 0
ffmpegAction = []
for chapter in chapters:
    startTimeCurrentChapter = chapter['time']

    timeForThisVideo = startTimeCurrentChapter % segmentDuration
    currentVideoIndex = int(startTimeCurrentChapter // segmentDuration)

    if chapter['advert']:
        saveVideoBeforeAdvert = ['./download/video{}.mp4'.format(currentVideoIndex), '-t', str(timeForThisVideo)]
        ffmpegAction.append(saveVideoBeforeAdvert)
        if startTimePreviousChapter > 0:
            videosWithoutAdvert ="|".join(['./download/video{}.mp4'.format(i) for i in range(previousVideoIndex, currentVideoIndex)])
            ffmpegAction.append('concat:{}'.format(videosWithoutAdvert))
    else:
        saveVideoAfterAdvert = ['./download/video{}.mp4'.format(currentVideoIndex), '-ss', str(timeForThisVideo)]
        ffmpegAction.append(saveVideoAfterAdvert)
    startTimePreviousChapter = startTimeCurrentChapter
    previousVideoIndex = int(currentVideoIndex if timeForThisVideo == 0 else currentVideoIndex + 1)


#previousVideoIndex = int(currentVideoIndex if timeForThisVideo == 0 else currentVideoIndex + 1)
if previousVideoIndex < len(urls):
    videosAfterLastAdvert ="|".join(['./download/video{}.mp4'.format(i) for i in range(previousVideoIndex, len(urls))])
    ffmpegAction.append('concat:{}'.format(videosAfterLastAdvert))

pprint.pprint(ffmpegAction)


#exit()


#http://toly.github.io/blog/2014/02/13/parallelism-in-one-line/
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

u = urls
par = zip(u, range(len(u)))
print par

if 1 == 0 :
    pool = ThreadPool(10)
    results = pool.map(videoDownload, par )
    pool.close()
    pool.join()
    print results




# videoClipsArray = ['./download/video{}.mp4'.format(i) for i in range(len(u))]
# videoClipsArg = "|".join(videoClipsArray)
# #print videoClipsArg
 
import subprocess
# ffmpeg_command1 = ["C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe", "-i", 'concat:{}'.format(videoClipsArg), "-c", "copy", "./result_video.mp4", "-y"]

# subprocess.call(ffmpeg_command1)

ffmpegCommands = [["C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe", "-i", ffmpegAction[i], "-c", "copy", "./download/part{}.ts".format(i), "-y"] for i in range(len(ffmpegAction))]

#two dimension array to one dimensions, fix arguments
for i in range(len(ffmpegCommands)):
    newCommand = []
    command = ffmpegCommands[i]

    for arg in command:
        if type(arg) is list:
            for partArg in arg:
                newCommand.append(partArg)
        else:
            newCommand.append(arg)
    ffmpegCommands[i] = newCommand

# for command in ffmpegCommands:
#     subprocess.call(command)
#print(ffmpegCommands[0])
#subprocess.call(ffmpegCommands[0])

pprint.pprint(ffmpegCommands)


if 1 == 1 :
    pool = ThreadPool()
    results = pool.map(subprocess.call, ffmpegCommands)
    pool.close()
    pool.join()
    print results

#print ffmpegCommands

videoPartsWithoutAdvert = "|".join(["./download/part{}.ts".format(i) for i in range(len(ffmpegCommands))])
ffmpegJoinAllPart = ["C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe", "-i", 'concat:{}'.format(videoPartsWithoutAdvert), "-c", "copy", "./result_video.mp4", "-y"]

subprocess.call(ffmpegJoinAllPart)