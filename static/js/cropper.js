// Interactive 4-corner perspective cropper with Loupe Magnifier
class DocumentCropper {
  constructor(canvasId, loupeCanvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.loupeCanvas = document.getElementById(loupeCanvasId);
    this.loupeCtx = this.loupeCanvas.getContext('2d');

    this.image = new Image();
    this.points = []; // [TL, TR, BR, BL] in image coordinates
    this.draggedIndex = -1;
    this.scale = 1.0;
    this.offsetX = 0;
    this.offsetY = 0;
    this.handleRadius = 14;

    this.initEvents();
  }

  loadImage(imageUrl, initialQuad = null) {
    return new Promise((resolve, reject) => {
      this.image.onload = () => {
        this.fitCanvasToContainer();
        if (initialQuad && initialQuad.length === 4) {
          this.points = JSON.parse(JSON.stringify(initialQuad));
        } else {
          this.resetToDefaults();
        }
        this.render();
        resolve();
      };
      this.image.onerror = reject;
      this.image.src = imageUrl;
    });
  }

  resetToDefaults() {
    const w = this.image.width;
    const h = this.image.height;
    const mx = w * 0.05;
    const my = h * 0.05;
    this.points = [
      [mx, my],
      [w - mx, my],
      [w - mx, h - my],
      [mx, h - my]
    ];
  }

  fitCanvasToContainer() {
    const container = this.canvas.parentElement;
    const rect = container.getBoundingClientRect();
    const availableW = rect.width;
    const availableH = rect.height;

    const imgAspect = this.image.width / this.image.height;
    const contAspect = availableW / availableH;

    let displayW, displayH;
    if (imgAspect > contAspect) {
      displayW = availableW;
      displayH = availableW / imgAspect;
    } else {
      displayH = availableH;
      displayW = availableH * imgAspect;
    }

    this.canvas.width = displayW;
    this.canvas.height = displayH;
    this.scale = displayW / this.image.width;
  }

  imgToCanvas(pt) {
    return [pt[0] * this.scale, pt[1] * this.scale];
  }

  canvasToImg(pt) {
    return [pt[0] / this.scale, pt[1] / this.scale];
  }

  render() {
    if (!this.image.complete) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 1. Disegna l'immagine base
    ctx.drawImage(this.image, 0, 0, this.canvas.width, this.canvas.height);

    if (this.points.length !== 4) return;

    // Converti coordinate in scala canvas
    const cPts = this.points.map(p => this.imgToCanvas(p));

    // 2. Disegna maschera scura semitrasparente all'esterno del poligono
    ctx.save();
    ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Rimuovi la maschera dentro il quadrilatero (clip)
    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.moveTo(cPts[0][0], cPts[0][1]);
    ctx.lineTo(cPts[1][0], cPts[1][1]);
    ctx.lineTo(cPts[2][0], cPts[2][1]);
    ctx.lineTo(cPts[3][0], cPts[3][1]);
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    // 3. Linee guida del contorno
    ctx.beginPath();
    ctx.moveTo(cPts[0][0], cPts[0][1]);
    ctx.lineTo(cPts[1][0], cPts[1][1]);
    ctx.lineTo(cPts[2][0], cPts[2][1]);
    ctx.lineTo(cPts[3][0], cPts[3][1]);
    ctx.closePath();
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = '#3b82f6';
    ctx.stroke();

    // 4. Maniglie d'angolo interattive
    const labels = ["TL", "TR", "BR", "BL"];
    cPts.forEach((pt, i) => {
      ctx.beginPath();
      ctx.arc(pt[0], pt[1], this.handleRadius, 0, Math.PI * 2);
      ctx.fillStyle = this.draggedIndex === i ? '#2563eb' : '#ffffff';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#3b82f6';
      ctx.stroke();

      // Centro punto
      ctx.beginPath();
      ctx.arc(pt[0], pt[1], 3, 0, Math.PI * 2);
      ctx.fillStyle = '#3b82f6';
      ctx.fill();
    });
  }

  updateLoupe(canvasX, canvasY, imgX, imgY) {
    if (!this.loupeCanvas) return;
    this.loupeCanvas.style.display = 'block';

    const lCtx = this.loupeCtx;
    const lW = this.loupeCanvas.width = 150;
    const lH = this.loupeCanvas.height = 150;
    lCtx.clearRect(0, 0, lW, lH);

    const zoom = 2.5;
    const srcSize = lW / zoom;

    lCtx.save();
    // Forma circolare
    lCtx.beginPath();
    lCtx.arc(lW / 2, lH / 2, lW / 2, 0, Math.PI * 2);
    lCtx.clip();

    // Disegna la porzione d'immagine ingrandita
    lCtx.drawImage(
      this.image,
      imgX - srcSize / 2, imgY - srcSize / 2, srcSize, srcSize,
      0, 0, lW, lH
    );

    // Mirino a croce
    lCtx.strokeStyle = '#ef4444';
    lCtx.lineWidth = 1.5;
    lCtx.beginPath();
    lCtx.moveTo(lW / 2, 0);
    lCtx.lineTo(lW / 2, lH);
    lCtx.moveTo(0, lH / 2);
    lCtx.lineTo(lW, lH / 2);
    lCtx.stroke();

    lCtx.restore();
  }

  hideLoupe() {
    if (this.loupeCanvas) {
      this.loupeCanvas.style.display = 'none';
    }
  }

  initEvents() {
    const getPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return [clientX - rect.left, clientY - rect.top];
    };

    const onStart = (e) => {
      const [cx, cy] = getPos(e);
      this.draggedIndex = -1;

      // Trova maniglia più vicina
      this.points.forEach((p, i) => {
        const [px, py] = this.imgToCanvas(p);
        const dist = Math.hypot(cx - px, cy - py);
        if (dist <= this.handleRadius * 1.8) {
          this.draggedIndex = i;
        }
      });

      if (this.draggedIndex !== -1) {
        e.preventDefault();
        const pt = this.points[this.draggedIndex];
        this.updateLoupe(cx, cy, pt[0], pt[1]);
        this.render();
      }
    };

    const onMove = (e) => {
      if (this.draggedIndex === -1) return;
      e.preventDefault();
      const [cx, cy] = getPos(e);

      // Limita ai bordi dell'immagine
      const clampedX = Math.max(0, Math.min(this.canvas.width, cx));
      const clampedY = Math.max(0, Math.min(this.canvas.height, cy));

      const [imgX, imgY] = this.canvasToImg([clampedX, clampedY]);
      this.points[this.draggedIndex] = [imgX, imgY];

      this.updateLoupe(cx, cy, imgX, imgY);
      this.render();
    };

    const onEnd = () => {
      if (this.draggedIndex !== -1) {
        this.draggedIndex = -1;
        this.hideLoupe();
        this.render();
      }
    };

    this.canvas.addEventListener('mousedown', onStart);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);

    this.canvas.addEventListener('touchstart', onStart, { passive: false });
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
    window.addEventListener('resize', () => {
      if (this.image.complete && this.image.width > 0) {
        this.fitCanvasToContainer();
        this.render();
      }
    });
  }

  getQuad() {
    return this.points;
  }
}
