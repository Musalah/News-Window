#!/bin/bash
# Verify the Snapchat data path, then sign and import "نافذة الأخبار" (macOS only).
set -euo pipefail
cd "$(dirname "$0")"

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
NAME="نافذة الأخبار"
WORK="$(mktemp -d)"

echo "== Step 1: verifying props.pageProps.story.snapList[].snapUrls.mediaUrl"
for account in trendnews24 saudi.panther; do
  curl -sSL -A "$UA" "https://www.snapchat.com/@$account" -o "$WORK/$account.html"
  perl -0ne 'print $1 if /__NEXT_DATA__[^>]*>(.*?)<\/script>/s' "$WORK/$account.html" > "$WORK/$account.json"
  osascript -l JavaScript -e '
    function run(argv) {
      const app = Application.currentApplication(); app.includeStandardAdditions = true;
      const raw = app.read(Path(argv[0]), {as: "«class utf8»"});
      if (!raw) return argv[1] + ": NO __NEXT_DATA__ found (page layout changed?)";
      const pp = JSON.parse(raw).props.pageProps;
      const snaps = pp.story && pp.story.snapList;
      if (!snaps) return argv[1] + ": no story.snapList (no current story, or path changed). pageProps keys: " + Object.keys(pp).join(", ");
      const urls = snaps.map(s => s.snapUrls && s.snapUrls.mediaUrl).filter(Boolean);
      return argv[1] + ": " + snaps.length + " snaps, " + urls.length + " mediaUrls" + (urls[0] ? "\n  e.g. " + urls[0] : "");
    }' "$WORK/$account.json" "$account"
done

echo "== Step 2: building"
if command -v python3 >/dev/null && python3 -c 'import plistlib' 2>/dev/null; then
  python3 build_shortcut.py "$WORK/unsigned.shortcut" >/dev/null
else
  cp news-window.unsigned.shortcut "$WORK/unsigned.shortcut"
fi

echo "== Step 3: signing and importing"
shortcuts sign --mode anyone --input "$WORK/unsigned.shortcut" --output "$WORK/$NAME.shortcut"
cp "$WORK/$NAME.shortcut" "./$NAME.shortcut"
open "./$NAME.shortcut"
echo "Done: tap 'Add Shortcut' in the Shortcuts window that just opened."
