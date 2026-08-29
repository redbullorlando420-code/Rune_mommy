export const PHOTO = {
  mira: {
    smile: "/portraits/mira-coffee.jpg",
    wink: "/portraits/mira-dinner.jpg",
    lean: "/portraits/mira-gown.jpg",
    heat: "/portraits/mira-lookback.jpg",
    blush: "/portraits/mira-stairs.jpg",
    tease: "/portraits/mira-courtyard.jpg",
    default: "/portraits/mira-coffee.jpg",
  },
  lila: {
    smile: "/portraits/lila-yoga.jpg",
    default: "/portraits/lila-yoga.jpg",
  },
};

export function paintPhoto(canvas, who, expr) {
  const pack = PHOTO[who];
  const url = pack && (pack[expr] || pack.default);
  if (!url) return false;
  const img = new Image();
  img.onload = () => {
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = true;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    ctx.drawImage(img, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
  };
  img.src = url;
  canvas.style.imageRendering = "auto";
  return true;
}
