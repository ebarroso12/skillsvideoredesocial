---
name: video-rabisco-lapis
description: Cria vídeos curtos verticais 9:16 (Reels, TikTok, Shorts) de NO MÁXIMO 60 segundos em estilo RABISCO preto e branco, em que uma mão com marcador/lápis DESENHA e ESCREVE na tela traço a traço sobre papel (frases, números, versículos, caricatura da pessoa ou personagem). Roteiro humano e empático, legenda queimada, marca d'água no canto inferior direito, tela final com chamada para consulta e legenda do post. Use SEMPRE que o usuário pedir vídeo de lápis/marcador desenhando, "rabisco", "desenho a mão", "preto e branco", "caneta escrevendo na tela", vídeo estilo lousa/sketch/whiteboard, caricatura em rabisco, ou quiser repetir o estilo do Reel DeKxI8Qj0aQ do Dr. Edson Barroso, mesmo que não diga "skill". Inclui motor com animação de desenho em Python + ffmpeg e trava de 60 s.
---

# Vídeo rabisco a lápis/marcador (até 60 s)

Transforma um tema (uma dor, uma mensagem, um versículo, uma lista de sinais) em um vídeo vertical
em que **uma mão desenha e escreve em tempo real** sobre papel claro, em preto e branco, com a
marca d'água no canto inferior direito, legenda e tela final de convite para a consulta.

Estilo de referência: Reel `DeKxI8Qj0aQ` do @dredsonbarroso — mão real segurando marcador preto,
linhas de tinta com hachura, números grandes desenhados, textos manuscritos e pequenas vinhetas
(ex.: homem acorrentado), papel com vinheta suave. Aqui o personagem pode ser a **caricatura da
pessoa** (ou um personagem escolhido) e o **contexto vem do que o usuário mandar**; cores não existem:
é tudo preto e branco.

## O que sai no final

1. `video_final.mp4` — 1080x1920, 30 fps, H.264 + AAC, **duração ≤ 60 s** (trava no script).
2. `legenda.txt` — legenda do post: texto empático + chamada para consulta + endereço/contato + hashtags.
3. O roteiro e os prompts das artes (para refazer ou ajustar).

## Por que o movimento do lápis fica "perfeito"

O motor `scripts/build_sketch_video.py` não faz "revelar com máscara": ele **refaz o gesto**.
A arte vira esqueleto (linha central de cada traço) → os traços são ordenados como um artista
(do topo para baixo, contornos grandes antes dos detalhes; texto na ordem de leitura) → a ponta
percorre cada traço sem saltos e **cada pixel de tinta só aparece quando a ponta passa por ele**.
Acelera e desacelera em cada traço, levanta em arco entre traços, treme levemente, a mão entra e sai
da tela e um chiado de marcador acompanha só quando a ponta toca o papel. Não precisa ajustar nada:
o que você controla é a **qualidade da arte** (veja a seção 3).

## Fluxo

Pergunte apenas o que faltar; se já deu tema, personagem e clima, comece.

### 0. Briefing (só o que faltar)

| Preciso saber | Se não disser |
|---|---|
| **Tema / dor** | pergunte — é o essencial |
| **Quem desenha**: (a) caricatura da própria pessoa (precisa da foto dela), (b) outro personagem/figura conhecida, (c) personagem original / só texto e símbolos | assuma (c) e avise |
| **Ferramenta**: `marcador` (preto, grosso — padrão), `lapis` (grafite) | marcador |
| **Voz**: gravada pelo usuário, narração gerada (grátis, offline) ou só legenda + música | gere a narração com `narrar_kokoro.py` (voz masculina pt-BR) e trilha com `gerar_trilha.py` |
| **Duração** | 35–50 s (limite 60 s, nunca ultrapasse) |

### 1. Roteiro

Siga `references/roteiro-empatico.md` (gancho → dor → acolhimento → perspectiva do médico → convite).
Este estilo funciona muito bem com **listas e números** ("3 sinais de que…") e **versículos/frases curtas**
escritos à mão. Misture cenas de texto (`escrever`) e cenas de desenho (`imagem`). Em cenas de texto, a
frase escrita deve ser CURTA (até ~8 palavras); a fala completa vai em `texto` (legenda).

### 2. Storyboard

- 6 a 10 cenas de 3,5 a 7 s (a tela final de 4,5 s entra automática).
- Alterne: frase manuscrita → desenho → número/lista → desenho → frase de acolhimento → convite.
- Cena com `escrever` + `imagem`: o texto é escrito no topo e depois o desenho embaixo.

### 3. Artes em linhas (o que alimenta o motor)

A arte de cada cena é um **PNG preto no branco** (ou fundo transparente), traço grosso e claro, pouca
hachura (centenas de traços viram um desenho demorado e "apressado"). Descubra o que o ambiente oferece:

1. **Arte enviada pelo usuário**: use direto.
2. **Foto enviada (caricatura/desenho da pessoa)**: rode
   `python3 <skill>/scripts/foto_para_rabisco.py foto.jpg cena_02.png --hachura` (offline, sem custo) ou, para
   caricatura exagerada de verdade, use um gerador de imagem com os prompts de `references/prompts-rabisco.md`.
3. **Gerador de imagem** (Claude: procure conectores com `SearchMcpRegistry`/`ToolSearch` "image generation";
   Codex/Manus: ferramenta nativa). Avise se consumir créditos antes de gerar em lote. Gere UMA arte de teste primeiro.
4. **Nada disponível**: entregue o storyboard com os prompts numerados e peça `cena_01.png`... ao usuário.
   Cenas só de texto (`escrever`) não precisam de imagem nenhuma.

Personagens: veja "Regras de personagem" e `references/personagens-conhecidos.md`.

### 4. Montagem

Crie `project.json` (modelo em `templates/project.example.json`) e rode a partir da pasta da skill:

```bash
python3 <skill>/scripts/build_sketch_video.py project.json --check-only   # plano de tempos
python3 <skill>/scripts/build_sketch_video.py project.json --preview      # teste rápido 540x960
python3 <skill>/scripts/build_sketch_video.py project.json                # versão final
```

Requisitos: `python3`, `pip install numpy scipy scikit-image opencv-python-headless pillow`, `ffmpeg` com libass.

| Campo | Para quê |
|---|---|
| `ferramenta` | `marcador` (padrão), `lapis` (mão com lápis cinza) ou `lapis-solto` (só o lápis, sem mão) |
| `cenas[].escrever` | texto escrito à mão (frase, número, versículo) |
| `cenas[].fonte` | `marcador` (padrão, forte), `manuscrito`, `pincel`, `caderno` |
| `cenas[].tamanho_escrita` | tamanho base em px (padrão 120; use 600–800 para um número grande) |
| `cenas[].imagem` | arte em linhas a desenhar |
| `cenas[].espessura` | espessura mínima do traço (padrão 5) |
| `cenas[].texto` | fala/legenda da cena; define o tempo (~2,6 palavras/s) |
| `cenas[].duracao` | opcional, em segundos |
| `legenda.ativa` / `legenda.posicao_y` | legenda queimada (padrão ligada, y=1470) |
| `audio.voz` / `audio.musica` | opcionais; com voz as cenas se esticam à fala |
| `audio.som_lapis` / `som_lapis_volume` | chiado do marcador (padrão ligado, 0,5) |
| `marca_dagua.cor` | `preto` (padrão, papel claro), `dourado`, `azul`, `branco` |
| `cta.ativo` / `cta.duracao` | tela final de consulta (padrão 4,5 s) |
| `post.corpo` | texto empático; o script monta o `legenda.txt` completo |
| `max_segundos` | limite (60) |

**Trava de 60 s**: se o plano passar, o script sai com código 2 e diz o excesso; sem voz, `--fit` comprime as cenas.
Nunca entregue acima de 60 s. No log, a linha de cada cena mostra traços, pixels e tempo de desenho; se aparecer
"muito rápido: simplifique a arte", a arte tem detalhe demais — gere uma versão com menos hachura.

#### Narração e trilha (grátis, offline)

```bash
pip install kokoro-onnx soundfile
python3 <skill>/scripts/narrar_kokoro.py project.json            # voz por cena (pm_alex; --voz pf_dora p/ feminina)
python3 <skill>/scripts/gerar_trilha.py trilha.wav --clima triste # trilha ambiente sem direitos autorais
```

`narrar_kokoro.py` grava `cenas[].voz`; com voz em todas as cenas o motor **ajusta o tempo de cada cena à fala**
(legenda sincronizada). Use `cenas[].fala` para o texto falado (se diferente da legenda `texto`). No `project.json`:
`"audio": {"musica": "trilha.wav", "musica_volume": 0.16, "som_lapis_volume": 0.35, "voz_volume": 1.15}`.
Modelos (~350 MB) baixam uma vez do GitHub para `~/.cache/skills-video/`. Se o usuário enviar a própria narração, use `audio.voz`.

### 5. Conferir antes de entregar

- Duração ≤ 60 s (o script valida).
- Extraia 3 a 4 quadros (`ffmpeg -ss 10 -i video_final.mp4 -frames:v 1 q.png`): a ponta do marcador está sobre o
  traço que acabou de aparecer? a mão não cobre o rosto o tempo todo? a legenda está legível? a marca d'água está
  no canto inferior direito?
- Ortografia e acentos das frases escritas e das legendas (as fontes manuscritas têm acentuação completa em PT-BR).

### 6. Entregar

MP4 + `legenda.txt` com uma linha de contexto e uma única próxima ação (ex.: versão com outro tema ou com voz).

## Regras de personagem

- **Caricatura da própria pessoa**: só com a foto que **ela** enviou; leve exagero respeitoso, nunca ridicularizante.
- **Terceiros e pacientes**: sem caricatura sem consentimento; em saúde nunca use imagem/história identificável de paciente.
- **Menores de idade**: personagem original, nunca caricatura de criança real.
- **Figuras e personagens conhecidos**: pesquise a descrição visual na web, não copie fotos de pessoas públicas.
  Personagens protegidos por direitos autorais não são reproduzidos fielmente: proponha um arquétipo original
  inspirado e diga isso em uma linha. Figuras públicas: caricatura respeitosa, nada de difamação ou política.
  Detalhes em `references/personagens-conhecidos.md`.

## Marca e identidade

Tudo vem de `brand/brand.json` e `brand/logos/` (nome, CRM, WhatsApp, endereço, site, Instagram, símbolos).
A marca d'água fica no **canto inferior direito** (13% da largura), símbolo preto por padrão (papel claro).
Para outra pessoa/clínica, troque o `brand.json` e os logos. Se os botões do Instagram cobrirem a marca, ajuste
`marca_dagua.margem_inferior_px` no projeto.

## Saúde mental e publicidade médica (checklist)

- Sem promessa de cura/resultado, sem antes e depois, sem depoimento de paciente, sem diagnóstico a distância.
- Acolhimento e convite à avaliação profissional, sem sensacionalismo nem medo.
- CRM visível (tela final e legenda — o script inclui).
- Tema com risco de autolesão/suicídio: sem métodos nem cenas gráficas (cuidado especial com desenhos de
  corpos acorrentados/enforcados: prefira metáforas como nós, âncoras, correntes soltas); na legenda do post,
  oriente buscar ajuda imediata (CVV 188, 24 h; SAMU 192).
- Versículos: cite a referência exata e não altere o texto bíblico.
- Dúvida sobre a norma vigente (Resolução CFM 2.336/2023): confira com o CRM; é lembrete prático, não parecer jurídico.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `ffmpeg não encontrado` / faltam bibliotecas | instale o ffmpeg e `pip install numpy scipy scikit-image opencv-python-headless pillow` |
| Erro de duração (código 2) | corte cenas/frases ou `--fit` (sem voz) |
| "Nada para desenhar" | a arte está clara/vazia: use traço preto sobre branco, mais grosso |
| Desenho "corre" demais | arte com detalhe/hachura demais: simplifique ou dê mais `duracao` à cena |
| Traço some/fica fraco | aumente `espessura` (6–8) |
| Mão cobre o rosto | ponha o rosto no terço superior e o resto da cena embaixo, ou use `ferramenta: lapis-solto` |
| Quer mão realista | substitua `assets/mao-marcador.png` (PNG com transparência; ponta no pixel indicado em `assets/sprites.json`) |

## Arquivos desta skill

- `scripts/build_sketch_video.py` — motor (esqueleto → caminho da caneta → animação → ffmpeg), tela final, legenda do post, trava de 60 s.
- `scripts/foto_para_rabisco.py` — foto → arte de linhas (offline).
- `scripts/narrar_kokoro.py`, `scripts/gerar_trilha.py` — narração pt-BR por cena e trilha ambiente (grátis, offline).
- `scripts/make_test_art.py`, `scripts/make_sprites.py` — arte de teste e gerador dos sprites da mão.
- `references/prompts-rabisco.md` — prompts para gerar a arte em linhas e a caricatura em rabisco.
- `references/roteiro-empatico.md`, `personagens-conhecidos.md`, `voz-e-audio.md` — roteiro, personagens, áudio.
- `templates/project.example.json` — modelo. `assets/` — mão+marcador, mão+lápis, lápis. `brand/`, `fonts/` — marca e fontes (OFL/Apache).
