# Dropzone Action Info
# Name: YouTube To MP3
# Description: Allows you to quickly download videos from YouTube and many other video sites. Downloaded videos are placed in the chosen folder.\n\nDownloads the highest quality version of the video and audio possible - This means the video and audio are sometimes downloaded seperately and the two files are automatically merged back together after the download completes.\n\nDrag a video URL onto the action or copy a URL onto the clipboard and then click the action to initiate download.
# Handles: Text
# Creator: Aptonic Software
# URL: https://aptonic.com
# OptionsNIB: ChooseFolder
# Events: Clicked, Dragged
# SkipConfig: No
# RunsSandboxed: No
# Version: 2.7
# MinDropzoneVersion: 3.5
# UniqueID: 1036

from __future__ import unicode_literals
import sys
import updater
import os
import traceback
import re
import utils


def dragged():
    download_url(items[0])


def clicked():
    url = dz.read_clipboard()
    download_url(url.decode('utf-8'))


def save_to_dropbar(file_path):
    dz.add_dropbar([file_path])


def download_url(url):
    regex = re.compile(
        r'^(?:http)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not regex.match(url):
        dz.fail("Not a valid video URL")

    dz.begin("Checking youtube-dl library is up to date...")
    utils.set_determinate_progress(False)

    updater.update_youtubedl()

    dz.begin("Preparing to download video...")
    utils.set_determinate_progress(False)
    utils.reset_progress()

    # Put ffmpeg in PATH for merging videos audio and video
    if 'apple_silicon' in os.environ:
        os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), 'ffmpeg-arm')
    else:
        os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), 'ffmpeg')

    # Download URL from clipboard
    sys.path.append("yt-dlp")

    from yt_dlp import YoutubeDL

    # Set download path to Dropzone temp folder
    print(dz.temp_folder())
    download_path = os.environ['path']

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'logger': MyLogger(),
        'progress_hooks': [my_hook]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            ydl_dict = ydl.extract_info(url, download=True)

        # Get full path of downloaded file
        req_dict = ydl_dict['requested_downloads'][0]
        file_path = req_dict['filepath']
        save_to_dropbar(file_path=file_path)


    except Exception as e:
        print(traceback.format_exc())
        dz.error("Video Download Failed", "Downloading video failed with the error:\n\n" + e.message)

    dz.finish("Video Download Complete")
    dz.url(False)


class MyLogger(object):
    def debug(self, msg):
        try:
            print(msg)
        except Exception:
            pass

    def warning(self, msg):
        try:
            print(msg)
        except Exception:
            pass

    def error(self, msg):
        try:
            print(msg)
        except Exception:
            pass


def my_hook(d):
    # print("test")
    # print(d['filename'])
    if d['status'] == 'downloading':
        speed_info = ""

        if 'filename' in d:
            filename = os.path.basename(d['filename'])
            print(f"filename: {filename}")
        else:
            filename = ""

        if '_eta_str' in d and '_speed_str' in d:
            speed_info = " (" + d['_speed_str'] + " ETA: " + d['_eta_str'] + ")"
        filename = filename.encode('ascii', 'ignore').decode('ascii')
        dz.begin("Downloading " + filename + speed_info + "...")
        total_bytes = 0

        if 'downloaded_bytes' in d:
            if 'total_bytes' in d:
                total_bytes = d['total_bytes']
            elif 'total_bytes_estimate' in d:
                total_bytes = d['total_bytes_estimate']

            percent = int(100 * d['downloaded_bytes'] / total_bytes)
            if percent > 0:
                utils.set_determinate_progress(True)
                utils.set_progress_percent(percent)

    if d['status'] == 'finished':
        utils.set_determinate_progress(False)
        utils.reset_progress()
        print('Download complete')
