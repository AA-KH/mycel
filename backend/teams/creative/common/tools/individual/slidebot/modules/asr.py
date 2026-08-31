"""
iFLYTEK ASR Module - Voice transcription functionality
"""

import os
import json
import base64
import hashlib
import hmac
import time
import urllib
import requests
from typing import Optional, List

from .config import XFYUN_APPID, XFYUN_SECRET_KEY, LFASR_HOST


class XfyunASR:
    """iFLYTEK non-real-time voice transcription API"""

    def __init__(self, appid: str, secret_key: str, upload_file_path: str):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = upload_file_path
        self.ts = str(int(time.time()))
        self.signa = self._get_signa()

    def _get_signa(self) -> str:
        """Generate signature"""
        m2 = hashlib.md5()
        m2.update((self.appid + self.ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        signa = hmac.new(self.secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        return str(signa, 'utf-8')

    def upload(self, num_speaker: Optional[int] = None) -> dict:
        """Upload audio file"""
        print("Uploading audio file...")
        file_len = os.path.getsize(self.upload_file_path)
        file_name = os.path.basename(self.upload_file_path)

        param_dict = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'fileSize': file_len,
            'fileName': file_name,
            'duration': '200',
            'roleType': 1,  # Enable speaker separation
            'pd': 'finance',  # Finance domain
        }

        # If user specified number of speakers, pass it in
        if num_speaker is not None:
            param_dict['roleNum'] = num_speaker

        print(f"Upload parameters: {param_dict}")

        data = open(self.upload_file_path, 'rb').read(file_len)
        response = requests.post(
            url=LFASR_HOST + '/upload?' + urllib.parse.urlencode(param_dict),
            headers={"Content-type": "application/json"},
            data=data
        )
        result = json.loads(response.text)
        print(f"Upload response: {result}")
        return result

    def get_result(self, num_speaker: Optional[int] = None) -> dict:
        """Get transcription result"""
        upload_resp = self.upload(num_speaker)

        if upload_resp.get('code') != '000000':
            return upload_resp

        order_id = upload_resp['content']['orderId']

        param_dict = {
            'appId': self.appid,
            'signa': self.signa,
            'ts': self.ts,
            'orderId': order_id,
            'resultType': 'transfer,predict',
        }

        print("Querying transcription result...")
        status = 3
        result = None

        # Poll for result
        while status == 3:
            response = requests.post(
                url=LFASR_HOST + '/getResult?' + urllib.parse.urlencode(param_dict),
                headers={"Content-type": "application/json"}
            )
            result = json.loads(response.text)
            status = result.get('content', {}).get('orderInfo', {}).get('status', 0)
            print(f"Status: {status}")

            if status == 4:
                break
            time.sleep(5)

        return result


def parse_xfyun_result(response_data: dict) -> List[dict]:
    """
    Parse iFLYTEK non-real-time voice transcription result
    :param response_data: Complete dictionary object returned by API
    :return: Parsed dialogue list [{"speaker": "Speaker 1", "text": "Content"}, ...]
    """
    if response_data.get('code') != '000000':
        print(f"API Error: {response_data.get('descInfo')}")
        return []

    content = response_data.get('content', {})
    order_result_str = content.get('orderResult')

    if not order_result_str:
        print("Transcription result is empty")
        return []

    try:
        order_result = json.loads(order_result_str)
    except json.JSONDecodeError:
        print("orderResult parsing failed")
        return []

    # Prioritize lattice
    lattices = order_result.get('lattice') or order_result.get('lattice2', [])

    dialogue_list = []

    for item in lattices:
        json_1best_str = item.get('json_1best', '{}')
        try:
            json_1best = json.loads(json_1best_str)
        except json.JSONDecodeError:
            continue

        st = json_1best.get('st', {})
        speaker_id = st.get('rl', '0')

        # Concatenate text
        segment_text = ""
        rt_list = st.get('rt', [])
        for rt in rt_list:
            ws_list = rt.get('ws', [])
            for ws in ws_list:
                cw_list = ws.get('cw', [])
                for cw in cw_list:
                    word = cw.get('w', '')
                    segment_text += word

        dialogue_list.append({
            "speaker": f"Speaker {speaker_id}",
            "text": segment_text,
            "bg": st.get('bg')
        })

    # Sort by time
    dialogue_list.sort(key=lambda x: int(x['bg']) if x['bg'] else 0)

    return dialogue_list


def format_dialogue_as_text(dialogue_list: List[dict]) -> str:
    """Format dialogue list as text"""
    lines = []
    for item in dialogue_list:
        lines.append(f"{item['speaker']}: {item['text']}")
    return "\n".join(lines)
