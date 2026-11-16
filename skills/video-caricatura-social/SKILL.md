---
name: video-caricatura-social
description: Cria vídeos curtos verticais 9:16 (Reels, TikTok, Shorts) de NO MÁXIMO 60 segundos a partir de um tema do usuário — roteiro humano e empático, cenas em caricatura/desenho (da própria pessoa, a partir da foto dela, ou de personagens conhecidos pesquisados), legenda dourada palavra por palavra, marca d'água da marca no canto inferior direito, tela final com chamada para consulta e a legenda do post. Use SEMPRE que o usuário pedir vídeo para Instagram/Reels/TikTok/Shorts, "vídeo caricatura", "transforme em caricatura ou desenho", vídeo ilustrado/animado com legenda, vídeo de saúde mental ou acolhimento, ou quiser repetir o estilo do Reel do Dr. Edson Barroso, mesmo que não diga "skill". Inclui script de montagem com ffmpeg e trava de duração de 60 s.
---

# Vídeo caricatura para redes sociais (até 60 s)

Transforma um tema (uma dor, uma mensagem, um conteúdo) em um vídeo vertical pronto para postar:
cenas ilustradas com movimento suave, legenda dourada palavra por palavra, marca d'água da marca no
canto inferior direito e uma tela final convidando para a consulta. Junto, entrega a legenda do post
no tom humano e empático.

O estilo de referência é o Reel do @dredsonbarroso (pintura fantástica, personagem pequeno diante de
paisagens grandes, legenda dourada serifada, narração emotiva), com uma diferença: o personagem passa
a ser a **caricatura da pessoa** (ou de outro personagem escolhido), e as **cores e o contexto vêm do
que o usuário mandar**.

## O que sai no final

1. `video_final.mp4` — 1080x1920, 30 fps, H.264 + AAC, **duração ≤ 60 s** (trava no script).
2. `legenda.txt` — legenda do post: texto empático + chamada para consulta + endereço/contato + hashtags.
3. O roteiro e os prompts das imagens (para o usuário poder refazer ou ajustar).

## Fluxo

Siga na ordem. Pergunte apenas o que faltar; se o usuário já deu tema, personagem e clima, não repita
perguntas, comece.

### 0. Briefing (só o que faltar)

| Preciso saber | Se não disser |
|---|---|
| **Tema / dor** que o vídeo toca (ex.: solidão, ansiedade, exaustão do cuidador) | pergunte — é o essencial |
| **Quem é o personagem**: (a) a caricatura da própria pessoa (precisa de foto), (b) outro personagem/figura conhecida, (c) um personagem original | assuma (c) e diga que assumiu |
| **Cores e contexto** (clima, cenário, época, paleta) | derive do tema e declare em uma linha |
| **Voz**: gravada pelo usuário, TTS do ambiente, ou só legenda + música | só legenda (+ música se enviada) |
| **Duração** | 35–50 s (o limite é 60 s, nunca ultrapasse) |

### 1. Roteiro

Escreva o roteiro seguindo `references/roteiro-empatico.md` (estrutura gancho → dor → acolhimento →
perspectiva do médico → convite; ~100 palavras para 40 s). A legenda do vídeo é o próprio roteiro, em
frases curtas, uma ideia por cena. Mostre o roteiro ao usuário junto com o storyboard (passo 2) e já
siga em frente, a menos que ele peça mudanças.

### 2. Storyboard e "ficha do personagem"

- 5 a 9 cenas de 4 a 7 s cada (a tela final de 4,5 s é adicionada pelo script).
- Escreva uma **ficha do personagem** (traços fixos: cabelo, óculos, barba, tom de pele, roupa, cores) e
  cole-a em TODOS os prompts, para o rosto não mudar entre cenas. Modelos em `references/prompts-imagem.md`.
- Regra de composição: personagem no terço superior/central e **espaço livre no terço inferior**, onde
  entra a legenda; deixe o canto inferior direito limpo (marca d'água).

### 3. Imagens (caricatura / desenho)

Descubra o que o ambiente oferece, nesta ordem:

1. **Imagens que o usuário enviou** (fotos ou artes): use direto, ou transforme a foto em caricatura/desenho
   com um gerador de imagem usando a foto como referência.
2. **Gerador de imagem disponível**: no Claude, procure conectores (`SearchMcpRegistry`/`ToolSearch` com
   "image generation"; há opções como Adobe Firefly, Figma e Gamma); no Codex e no Manus, use a
   ferramenta nativa de geração de imagem. Avise o usuário se a ferramenta consumir créditos antes de gerar em lote.
3. **Nenhum gerador**: entregue o storyboard com os prompts numerados e peça ao usuário para gerar/enviar
   as imagens (`cena_01.png`, `cena_02.png`...). Continue a partir daí.

Gere primeiro **uma** imagem de teste (cena 1), confira o rosto e o estilo, só então gere as demais.
Formato 9:16 (ex.: 1080x1920 ou maior). Se vier em outra proporção, o script faz fundo desfocado.

Personagens: veja "Regras de personagem" abaixo e `references/personagens-conhecidos.md`.

### 4. Montagem

Crie `project.json` (modelo em `templates/project.example.json`) e rode o script **a partir da pasta onde
esta skill está instalada** (a que contém este SKILL.md):

```bash
python3 <pasta-da-skill>/scripts/build_video.py project.json --check-only   # plano de tempos
python3 <pasta-da-skill>/scripts/build_video.py project.json --preview      # teste rápido 540x960
python3 <pasta-da-skill>/scripts/build_video.py project.json                # versão final
```

Requisitos: `python3`, `pip install pillow`, `ffmpeg` com libass (o padrão da maioria das instalações).

Campos principais do `project.json` (todos os caminhos relativos à pasta do projeto):

| Campo | Para quê |
|---|---|
| `cenas[].imagem` / `texto` | imagem da cena e a frase que vira legenda |
| `cenas[].duracao` | opcional; sem ela o tempo vem do nº de palavras (~2,6 palavras/s) |
| `cenas[].movimento` | `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`, `none` |
| `cenas[].ajuste` | `auto` (padrão), `cover` (corta) ou `blur` (fundo desfocado) |
| `audio.voz` / `audio.musica` | arquivos opcionais; com voz, as cenas se esticam até o fim da fala |
| `legenda.posicao_y` | altura da legenda em px (padrão 1280, no terço inferior) |
| `marca_dagua.cor` | `auto` (padrão: escolhe por contraste), `dourado`, `branco`, `azul`, `preto` |
| `cta.ativo` / `cta.duracao` | tela final com a chamada para consulta (padrão 4,5 s) |
| `post.corpo` | texto empático do post; o script monta o `legenda.txt` completo |
| `max_segundos` | limite; padrão 60 |

**Trava de 60 s:** se o plano passar do limite o script para com erro (código 2) e diz quanto excedeu.
Sem voz, `--fit` comprime as cenas. Com voz, corte o texto e regrave. Nunca entregue um vídeo acima de 60 s.

### 5. Conferir antes de entregar

- Duração do MP4 final ≤ 60 s (o script já imprime e valida).
- Extraia 3 quadros (início, meio, fim) e olhe: legenda legível sobre o fundo, sem cobrir o rosto;
  marca d'água visível no canto inferior direito; tela final completa.
  `ffmpeg -ss 10 -i video_final.mp4 -frames:v 1 quadro.png`
- Releia as legendas: acentuação e ortografia corretas.
- Rosto do personagem consistente entre cenas.

### 6. Entregar

Envie o MP4 e o `legenda.txt` com uma linha de contexto. Ofereça uma única próxima ação (ex.: uma versão
com outro cenário ou com a voz dele). Se o ambiente tiver ferramenta de envio de arquivos, use-a; senão
informe o caminho dos arquivos.

## Regras de personagem

- **Caricatura da própria pessoa**: só com a foto que **ela** enviou. Preserve traços marcantes (cabelo,
  barba, óculos, tom de pele, formato do rosto) com leve exagero respeitoso e simpático, nunca ridicularizante.
- **Pessoas privadas**: nada de caricaturar terceiros (pacientes, familiares) sem consentimento da pessoa;
  em conteúdo de saúde, nunca use imagem ou história identificável de paciente.
- **Menores de idade**: sem caricatura de crianças reais; use personagem original.
- **Personagens/figuras conhecidas**: pesquise a descrição visual na web (traços, cores, figurino) e use
  como inspiração. Não baixe nem copie fotos de pessoas públicas. Personagens protegidos por direitos
  autorais (desenhos, filmes, jogos) muitas vezes são recusados pelos geradores e não devem ser
  reproduzidos fielmente: proponha um **arquétipo original inspirado** (ex.: "guerreiro de capa azul")
  e explique em uma linha. Para figuras públicas reais, caricatura respeitosa; nada de difamação, de
  ataque político ou de afirmações falsas atribuídas à pessoa. Detalhes em `references/personagens-conhecidos.md`.

## Marca e identidade

Tudo sai de `brand/brand.json` e `brand/logos/`: nome, CRM, WhatsApp, endereço, site, Instagram, cores e
marcas d'água (símbolo dourado, branco, azul e preto) já gravados. A marca d'água fica no **canto inferior
direito** (13% da largura) e a cor é escolhida pelo contraste com o fundo. Para usar com outra
pessoa/clínica, troque o `brand.json` e os arquivos de `brand/logos/` (mantendo os nomes ou ajustando o JSON).

Observação de layout: no Instagram, os botões laterais e a legenda do post podem cobrir parte do canto
inferior direito; se a marca ficar escondida, ajuste `marca_dagua.margem_inferior_px` no projeto.

## Saúde mental e publicidade médica (checklist)

Conteúdo de saúde exige cuidado. Antes de entregar, confirme:

- Sem promessa de cura ou resultado, sem "antes e depois", sem depoimento de paciente, sem diagnóstico a distância.
- Linguagem de acolhimento e convite à avaliação profissional, sem sensacionalismo nem medo.
- Registro profissional visível (CRM na tela final e na legenda; o script já inclui).
- Se o tema envolver risco de autolesão ou suicídio: não mostre métodos nem cenas gráficas; inclua na
  legenda do post a orientação de procurar ajuda imediata (CVV 188, 24 h; SAMU 192 em emergência).
- Em dúvida sobre a norma vigente (Resolução CFM 2.336/2023 sobre publicidade médica), diga ao usuário
  para conferir com o CRM; isto é um lembrete prático, não parecer jurídico.

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `ffmpeg não encontrado` | instale o ffmpeg e reabra o terminal |
| Legenda sem a fonte dourada serifada | a pasta `fonts/` deve acompanhar o script (não mova o script sozinho) |
| Erro de duração (código 2) | roteiro longo: corte frases, reduza cenas, ou `--fit` (sem voz) |
| Rosto muda de cena para cena | reuse a mesma ficha do personagem e gere a partir de uma imagem de referência |
| Marca d'água some no fundo | `marca_dagua.cor` manual (`branco`/`azul`/`dourado`) |
| Texto cobre o rosto | aumente `legenda.posicao_y` ou refaça a imagem com espaço livre embaixo |

## Arquivos desta skill

- `scripts/build_video.py` — montagem do vídeo, tela final, legenda do post e trava de 60 s.
- `scripts/make_test_scenes.py` — gera cenas sintéticas só para testar o motor (não é arte final).
- `references/roteiro-empatico.md` — estrutura do roteiro, tom, modelo da legenda do post, hashtags.
- `references/prompts-imagem.md` — ficha do personagem, bloco de estilo, prompts de cena e de caricatura.
- `references/personagens-conhecidos.md` — como pesquisar e adaptar personagens e figuras conhecidas.
- `references/voz-e-audio.md` — opções de narração e música.
- `references/instalacao.md` — instalação no Claude Code, Codex, Manus e Claude.ai.
- `templates/project.example.json` — modelo do projeto.
- `brand/` e `fonts/` — marca, logos e fontes (Playfair Display e Montserrat, licença OFL).
