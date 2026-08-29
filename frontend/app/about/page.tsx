export default function AboutPage() {
  return (
    <div className="p-6 md:p-10 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">About AreebFetch</h1>
      <p className="text-[hsl(var(--muted-foreground))] leading-relaxed">
        AreebFetch is an all-in-one media & document studio: video/audio downloader,
        image tools, PDF tools, and CamScanner-style document scanning — self-hosted.
      </p>
      <ul className="list-disc pl-5 space-y-1 text-sm text-[hsl(var(--muted-foreground))]">
        <li>1000+ sites via yt-dlp (incl. 4K)</li>
        <li>Audio extract, batch & playlist detect</li>
        <li>Image compress / resize</li>
        <li>PDF merge, split, compress</li>
        <li>Document scanner (edge crop + enhance → PDF)</li>
        <li>File manager + local downloads folder</li>
        <li>OLED / 3D dark theme</li>
      </ul>
      <p className="text-xs text-[hsl(var(--muted-foreground))] pt-4 border-t border-[hsl(var(--border))]">
        Personal / educational use. Respect copyright. No DRM circumvention.
      </p>
      <p className="text-xs opacity-60">AreebFetch v1.2.0 · yt-dlp 2026.8.19</p>
    </div>
  );
}
