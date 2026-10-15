// Webcam capture controller for direct document scanning
class CameraScanner {
  constructor(videoElementId, onCaptureCallback) {
    this.video = document.getElementById(videoElementId);
    this.onCapture = onCaptureCallback;
    this.stream = null;
    this.capturedCount = 0;
  }

  async start() {
    this.capturedCount = 0;
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          facingMode: "environment"
        },
        audio: false
      });
      this.video.srcObject = this.stream;
      await this.video.play();
      return true;
    } catch (err) {
      console.error("Errore accesso fotocamera:", err);
      throw err;
    }
  }

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.video) {
      this.video.srcObject = null;
    }
  }

  captureFrame() {
    if (!this.stream || this.video.videoWidth === 0) return null;

    const canvas = document.createElement('canvas');
    canvas.width = this.video.videoWidth;
    canvas.height = this.video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(this.video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
    this.capturedCount++;

    if (this.onCapture) {
      this.onCapture(dataUrl, this.capturedCount);
    }

    return dataUrl;
  }
}
