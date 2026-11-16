# Prompts para a arte em linhas (rabisco preto e branco)

A arte precisa ser **fácil de desenhar traço a traço**: contorno firme, pouca hachura, fundo branco liso, sem cinza,
sem cor, sem texto dentro da imagem (o texto é escrito pelo motor).

## Bloco de estilo (cole em todos os prompts)

> Black marker ink line drawing on pure white background, hand-drawn sketch style with bold confident outlines
> (thick uniform strokes), minimal cross-hatching for shadows, expressive cartoon/caricature proportions,
> no colors, no gray fills, no background scenery unless stated, no text, no watermark, vertical composition,
> subject centered with generous empty margins.

## Ficha do personagem (repita em todas as cenas)

> [Nome/idade aproximada], [cabelo], [barba/óculos], [formato do rosto], [roupa], [traço marcante]. Same character in every image.

## Prompts de cena (exemplos)

- Abertura: *[ficha], sitting alone on a bench with head down, small figure, large empty space around. [bloco de estilo]*
- Peso emocional: *[ficha], shoulders bent under a huge stone on his back tied with a rope, simple ground line. [bloco de estilo]*
- Acolhimento: *[ficha], a helping hand reaching down from the top edge toward him, he looks up. [bloco de estilo]*
- Esperança: *[ficha], standing straight, chains broken and lying on the floor, a small sun drawn with simple rays. [bloco de estilo]*

## Caricatura a partir da foto da própria pessoa

> Turn the attached photo into a black marker line caricature: keep the distinctive hair, beard, glasses and face
> shape, slightly exaggerated head, friendly respectful expression, bold outlines, light hatching only. [bloco de estilo]

Sem gerador de imagem: `python3 scripts/foto_para_rabisco.py foto.jpg arte.png --hachura` (contorno fiel, sem exagero).

## Checagem da arte antes de montar

- Fundo branco puro; traço preto sólido; nenhuma sombra em cinza.
- Menos de ~12 mil pixels de traço depois de reduzida (arte simples = desenho lento e bonito).
- Rosto no terço superior (a mão entra pela direita e pode cobrir a parte de baixo).
- Evite métodos ou cenas gráficas de autolesão: use metáforas (nós, âncoras, correntes soltas).
