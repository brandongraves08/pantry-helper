import { useEffect, useRef, useState } from 'react';
import { Camera, X, Loader, ScanLine } from 'lucide-react';

/**
 * Phone camera barcode scanner component.
 *
 * Uses the Web Barcode Detection API (Chrome Android) as primary path,
 * with the html5-qrcode library as a universal fallback.
 */
export default function CameraScanner({ onDetected, onClose }) {
  const [status, setStatus] = useState('initializing'); // initializing | scanning | detected | error
  const [support, setSupport] = useState(null); // 'native' | 'library' | null
  const scannerRef = useRef(null);
  const videoRef = useRef(null);

  useEffect(() => {
    startScanning();
    return () => stopScanning();
  }, []);

  const startScanning = async () => {
    // Try native BarcodeDetector API first
    if ('BarcodeDetector' in window) {
      setSupport('native');
      await startNativeScan();
    }
    // Fall back to html5-qrcode library
    else {
      setSupport('library');
      await startLibraryScan();
    }
  };

  const startNativeScan = async () => {
    setStatus('initializing');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
      });

      const video = document.createElement('video');
      videoRef.current = video;
      video.srcObject = stream;
      video.setAttribute('playsinline', '');
      video.setAttribute('autoplay', '');
      video.setAttribute('muted', '');

      // Mount video into the viewfinder
      const container = document.getElementById('camera-viewfinder');
      if (container) {
        container.innerHTML = '';
        container.appendChild(video);
      }

      await video.play();
      setStatus('scanning');

      const detector = new BarcodeDetector({ formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'codabar', 'itf', 'qr_code'] });

      // Scan loop
      let running = true;
      scannerRef.current = { running, detector, stream, video };

      const scanLoop = async () => {
        while (scannerRef.current?.running) {
          try {
            const barcodes = await detector.detect(video);
            if (barcodes.length > 0) {
              const code = barcodes[0].rawValue;
              if (code && code.length >= 8) {
                scannerRef.current.running = false;
                setStatus('detected');
                const tracks = stream.getTracks();
                tracks.forEach(t => t.stop());
                onDetected(code);
                return;
              }
            }
          } catch {
            // Frame decode errors are normal, keep going
          }
          // Yield every frame cycle
          await new Promise(r => requestAnimationFrame(r));
        }
      };

      scanLoop();
    } catch (err) {
      console.error('Native barcode scan failed:', err);
      // Try library fallback
      setSupport('library');
      await startLibraryScan();
    }
  };

  const startLibraryScan = async () => {
    setStatus('initializing');
    try {
      const { Html5Qrcode } = await import('html5-qrcode');

      const scanner = new Html5Qrcode('camera-viewfinder');
      scannerRef.current = { scanner, running: true };

      await scanner.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 250, height: 150 },
          formatsToSupport: [
            Html5Qrcode.SCAN_FORMATS.EAN_13,
            Html5Qrcode.SCAN_FORMATS.EAN_8,
            Html5Qrcode.SCAN_FORMATS.UPC_A,
            Html5Qrcode.SCAN_FORMATS.UPC_E,
            Html5Qrcode.SCAN_FORMATS.CODE_128,
            Html5Qrcode.SCAN_FORMATS.CODE_39,
            Html5Qrcode.SCAN_FORMATS.CODABAR,
            Html5Qrcode.SCAN_FORMATS.ITF,
          ],
        },
        (decodedText) => {
          if (decodedText && decodedText.length >= 8) {
            scannerRef.current.running = false;
            setStatus('detected');
            scanner.stop().catch(() => {});
            onDetected(decodedText);
          }
        },
        () => { /* frame not decoded — normal */ }
      );

      setStatus('scanning');
    } catch (err) {
      console.error('Camera scan failed:', err);
      setStatus('error');
    }
  };

  const stopScanning = async () => {
    if (scannerRef.current) {
      if (scannerRef.current.stream) {
        scannerRef.current.stream.getTracks().forEach(t => t.stop());
      }
      if (scannerRef.current.scanner && typeof scannerRef.current.scanner.stop === 'function') {
        try { await scannerRef.current.scanner.stop(); } catch {}
      }
      scannerRef.current.running = false;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/80">
        <h3 className="text-white font-semibold">Scan Barcode</h3>
        <button onClick={() => { stopScanning(); onClose(); }} className="p-2 text-white/80 hover:text-white">
          <X size={24} />
        </button>
      </div>

      {/* Viewfinder */}
      <div className="flex-1 relative flex items-center justify-center bg-black">
        <div id="camera-viewfinder" className="w-full max-w-md aspect-[4/3] relative">
          {status === 'initializing' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white gap-3">
              <Loader size={36} className="animate-spin text-blue-400" />
              <p className="text-sm text-gray-300">Starting camera...</p>
            </div>
          )}
          {status === 'scanning' && (
            <div className="absolute inset-0 pointer-events-none">
              {/* Scan overlay */}
              <div className="absolute inset-x-[15%] top-1/4 bottom-1/4 border-2 border-blue-400 rounded-xl">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded">
                  <ScanLine size={14} className="inline mr-1" />
                  Point at barcode
                </div>
                {/* Scanning line animation */}
                <div className="absolute left-0 right-0 h-0.5 bg-blue-400 animate-scan-line" />
              </div>
            </div>
          )}
          {status === 'error' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white gap-3">
              <Camera size={48} className="text-gray-500" />
              <p className="text-sm text-gray-400">Camera not available</p>
              <p className="text-xs text-gray-500">Check camera permissions and try again</p>
              <button onClick={onClose} className="px-4 py-2 bg-gray-800 rounded-lg text-sm mt-2">
                Close
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom info */}
      <div className="px-4 py-4 bg-black/80 text-center">
        <p className="text-gray-400 text-xs">
          Point your camera at a barcode to scan it.
          Works best with EAN-13 and UPC-A codes.
        </p>
      </div>
    </div>
  );
}
