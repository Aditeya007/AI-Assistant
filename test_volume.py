"""Test script to verify pycaw volume control"""
import comtypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def test_volume():
    try:
        print("Initializing COM...")
        comtypes.CoInitialize()
        
        print("Getting speakers...")
        devices = AudioUtilities.GetSpeakers()
        print(f"Device type: {type(devices)}")
        print(f"Device: {devices}")
        
        # Check if device has Activate method
        if hasattr(devices, 'Activate'):
            print("✓ Device has Activate method")
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Get current volume
            current = volume.GetMasterVolumeLevelScalar()
            print(f"Current volume: {current * 100}%")
            
            # Test setting volume to 50%
            print("Setting volume to 50%...")
            volume.SetMasterVolumeLevelScalar(0.5, None)
            
            # Verify
            new_vol = volume.GetMasterVolumeLevelScalar()
            print(f"New volume: {new_vol * 100}%")
            print("✓ Volume control works!")
        else:
            print("✗ Device does NOT have Activate method")
            print(f"Available methods: {dir(devices)}")
        
        comtypes.CoUninitialize()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            comtypes.CoUninitialize()
        except:
            pass

if __name__ == "__main__":
    test_volume()
