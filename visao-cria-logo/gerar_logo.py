"""Gera o logo "Visão Cria" (servidor FiveM) em SVG, com o texto convertido em curvas.

Uso: python3 gerar_logo.py  (requer: pip install fonttools)
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONTE = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
font = TTFont(FONTE)
gs = font.getGlyphSet()
cmap = font.getBestCmap()
upm = font["head"].unitsPerEm
hmtx = font["hmtx"]


def texto(s, cx, baseline, size, espaco=0, largura_max=None):
    """Retorna (path_d, largura) do texto centralizado em cx."""
    nomes = [cmap[ord(c)] for c in s]
    esc = size / upm
    larg = sum(hmtx[n][0] for n in nomes) * esc + espaco * (len(nomes) - 1)
    if largura_max and larg > largura_max:
        f = largura_max / larg
        return texto(s, cx, baseline, size * f, espaco * f)
    x = cx - larg / 2
    pen = SVGPathPen(gs)
    for n in nomes:
        tp = TransformPen(pen, (esc, 0, 0, -esc, x, baseline))
        gs[n].draw(tp)
        x += hmtx[n][0] * esc + espaco
    return pen.getCommands(), larg


visao, _ = texto("VISÃO", 512, 640, 220, espaco=4, largura_max=780)
cria, _ = texto("CRIA", 512, 752, 92, espaco=34)
rp, _ = texto("ROLEPLAY", 512, 846, 30, espaco=14)


def svg(fundo: bool) -> str:
    bg = '<rect width="1024" height="1024" fill="url(#bg)"/>' if fundo else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
  <defs>
    <radialGradient id="bg" cx="50%" cy="45%" r="70%">
      <stop offset="0" stop-color="#1c0b33"/><stop offset="1" stop-color="#05020a"/>
    </radialGradient>
    <radialGradient id="disco" cx="50%" cy="35%" r="65%">
      <stop offset="0" stop-color="#2a0f4d"/><stop offset="1" stop-color="#0b0416"/>
    </radialGradient>
    <linearGradient id="anel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#e3b8ff"/><stop offset=".45" stop-color="#9b30ff"/><stop offset="1" stop-color="#4a0d8f"/>
    </linearGradient>
    <linearGradient id="letra" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#e6ccff"/><stop offset="1" stop-color="#b86bff"/>
    </linearGradient>
    <linearGradient id="faixa" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#5b10b0"/><stop offset=".5" stop-color="#a033ff"/><stop offset="1" stop-color="#5b10b0"/>
    </linearGradient>
    <radialGradient id="iris" cx="45%" cy="40%" r="60%">
      <stop offset="0" stop-color="#f0d6ff"/><stop offset=".35" stop-color="#b14dff"/><stop offset="1" stop-color="#3d0a7a"/>
    </radialGradient>
    <filter id="brilho" filterUnits="userSpaceOnUse" x="0" y="0" width="1024" height="1024">
      <feGaussianBlur stdDeviation="14" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="sombra" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000" flood-opacity=".75"/>
    </filter>
    <clipPath id="olhoClip"><path d="M322 330 Q512 180 702 330 Q512 480 322 330Z"/></clipPath>
  </defs>
  {bg}
  <!-- emblema -->
  <circle cx="512" cy="470" r="430" fill="#9b30ff" opacity=".18" filter="url(#brilho)"/>
  <circle cx="512" cy="470" r="420" fill="url(#disco)" stroke="url(#anel)" stroke-width="20"/>
  <circle cx="512" cy="470" r="388" fill="none" stroke="#9b30ff" stroke-opacity=".45" stroke-width="3" stroke-dasharray="2 14" stroke-linecap="round"/>
  <!-- raios acima do olho -->
  <g stroke="#b866ff" stroke-width="10" stroke-linecap="round" filter="url(#brilho)">
    <line x1="512" y1="150" x2="512" y2="200"/>
    <line x1="420" y1="168" x2="440" y2="212"/>
    <line x1="604" y1="168" x2="584" y2="212"/>
    <line x1="340" y1="208" x2="372" y2="244"/>
    <line x1="684" y1="208" x2="652" y2="244"/>
  </g>
  <!-- olho (visão) -->
  <g filter="url(#brilho)">
    <path d="M322 330 Q512 180 702 330 Q512 480 322 330Z" fill="#0b0416" stroke="url(#anel)" stroke-width="14" stroke-linejoin="round"/>
    <g clip-path="url(#olhoClip)">
      <circle cx="512" cy="330" r="82" fill="url(#iris)"/>
      <circle cx="512" cy="330" r="82" fill="none" stroke="#2a0652" stroke-width="6"/>
      <circle cx="512" cy="330" r="34" fill="#07020d"/>
      <circle cx="534" cy="306" r="13" fill="#fff"/>
      <circle cx="490" cy="352" r="6" fill="#fff" opacity=".7"/>
    </g>
  </g>
  <!-- VISÃO -->
  <g filter="url(#sombra)">
    <path d="{visao}" fill="none" stroke="#12051f" stroke-width="22" stroke-linejoin="round"/>
    <path d="{visao}" fill="url(#letra)" stroke="#7a1fd6" stroke-width="3"/>
  </g>
  <!-- faixa CRIA -->
  <g filter="url(#sombra)">
    <path d="M258 668 L790 668 L766 774 L234 774 Z" fill="url(#faixa)" stroke="#e3b8ff" stroke-width="5" stroke-linejoin="round"/>
    <path d="M208 690 L248 690 L232 758 L192 758 Z" fill="#9b30ff"/>
    <path d="M816 690 L856 690 L840 758 L800 758 Z" fill="#9b30ff"/>
    <path d="{cria}" fill="#ffffff"/>
  </g>
  <!-- ROLEPLAY -->
  <path d="{rp}" fill="#c48bff"/>
  <g fill="#c48bff">
    <path d="M330 834 l8 -8 8 8 -8 8z"/><path d="M678 834 l8 -8 8 8 -8 8z"/>
  </g>
</svg>
'''


saida = Path(__file__).parent
(saida / "visao-cria-logo.svg").write_text(svg(False), encoding="utf-8")
(saida / "visao-cria-logo-fundo.svg").write_text(svg(True), encoding="utf-8")
print("ok")
