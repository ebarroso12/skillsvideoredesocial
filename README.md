# skillsvideoredesocial

Skill **`video-caricatura-social`**: transforma um tema em um **vídeo vertical (9:16) de no máximo 60 segundos**
para Reels, TikTok e Shorts, no estilo do Reel do [@dredsonbarroso](https://www.instagram.com/dredsonbarroso/):
cenas ilustradas (pintura/caricatura) com movimento suave, **legenda dourada palavra por palavra**,
**marca d'água no canto inferior direito**, **tela final com chamada para consulta** e a **legenda do post**
em tom humano e empático.

- O personagem pode ser a **caricatura da própria pessoa** (a partir da foto dela) ou de **outros personagens**
  (pesquisados; sem copiar personagens protegidos).
- **Cores e contexto** vêm do que o usuário pedir.
- **Nunca passa de 60 s**: o script bloqueia o render se o roteiro estourar o limite.
- Funciona no **Claude Code, Codex, Manus** e no Claude.ai (formato aberto de skills).

## Instalar

### Claude Code (plugin)

```
/plugin marketplace add ebarroso12/skillsvideoredesocial
/plugin install video-caricatura-social@skillsvideoredesocial
```

### Qualquer ferramenta (cópia da pasta)

```bash
git clone https://github.com/ebarroso12/skillsvideoredesocial.git
cd skillsvideoredesocial
./install.sh                  # Claude Code  (~/.claude/skills)
./install.sh --target codex   # Codex        (~/.codex/skills)
./install.sh --target agents  # pasta genérica (~/.agents/skills)
./install.sh --target all     # os três
./install.sh --project        # só no projeto atual
```

Windows: `.\install.ps1` (ou `-Target codex`).

### Manus e Claude.ai (upload de ZIP)

Use `dist/video-caricatura-social.zip` (importe em Skills). Mais detalhes em
[`skills/video-caricatura-social/references/instalacao.md`](skills/video-caricatura-social/references/instalacao.md).

### Requisitos para montar o vídeo

`python3`, `pip install pillow` e `ffmpeg` (com libass). Sem eles a skill ainda entrega roteiro, prompts e legenda.

## Como usar

Diga, por exemplo:

> Crie um vídeo caricatura de 45 segundos para o Reels sobre solidão de quem tenta ser forte todo dia.
> Use a minha caricatura (foto em anexo), cores azul-noite e dourado.

> Quero um vídeo com um guerreiro medieval falando de ansiedade, tons terrosos, até 40 segundos.

A skill pergunta só o que faltar e segue: **roteiro → storyboard e prompts → imagens → montagem → conferência → entrega**
(MP4 + `legenda.txt`).

As imagens vêm de (1) fotos/artes que você enviar, (2) um gerador de imagem disponível no ambiente
(conectores no Claude, ferramenta nativa no Codex/Manus) ou (3) imagens que você gerar a partir dos prompts entregues.

## Estrutura

```
skills/video-caricatura-social/
├── SKILL.md                    instruções e fluxo
├── scripts/build_video.py      montagem (ffmpeg), tela final, legenda do post, trava de 60 s
├── scripts/make_test_scenes.py cenas sintéticas só para testar o motor
├── references/                 roteiro empático, prompts, personagens, áudio, instalação
├── templates/project.example.json
├── brand/brand.json            dados da marca (CRM, contatos, cores)
├── brand/logos/                12 marcas (horizontal, vertical, símbolo; dourada/branca/azul/preta)
├── fonts/                      Playfair Display e Montserrat (OFL)
└── evals/                      casos de teste
```

## Usar com outra marca

Troque `brand/brand.json` e os PNG de `brand/logos/` (mantenha os nomes ou ajuste `marca_dagua.variantes`).

## Aviso

Conteúdo de saúde segue regras do conselho profissional (no Brasil, Resolução CFM 2.336/2023 sobre publicidade
médica): sem promessa de resultado, sem antes e depois, sem depoimentos, com CRM visível. A skill traz um
checklist, mas a responsabilidade pelo conteúdo publicado é de quem publica.

## Licenças

Código: uso livre pelo proprietário do repositório. Fontes Playfair Display e Montserrat: SIL Open Font License 1.1
(ver `skills/video-caricatura-social/fonts/OFL-PlayfairDisplay.txt e fonts/OFL-Montserrat.txt`). Marca e logotipos do Dr. Edson Barroso: todos os direitos reservados.
