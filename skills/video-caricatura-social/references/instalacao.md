# Instalação por plataforma

A skill segue o formato aberto de Agent Skills (pasta com `SKILL.md`), então a mesma pasta funciona em
várias ferramentas. Requisitos de execução em qualquer uma: `python3`, `pip install pillow` e `ffmpeg`.

## Claude Code

Opção A, plugin (recomendada; atualiza com `git`):

```
/plugin marketplace add ebarroso12/skillsvideoredesocial
/plugin install video-caricatura-social@skillsvideoredesocial
```

Opção B, cópia direta:

```bash
git clone https://github.com/ebarroso12/skillsvideoredesocial.git
cd skillsvideoredesocial
./install.sh                 # instala em ~/.claude/skills
./install.sh --project       # ou só no projeto atual (.claude/skills)
```

## Codex (OpenAI)

```bash
./install.sh --target codex      # ~/.codex/skills/video-caricatura-social
# ou, se a sua versão lê ~/.agents/skills:
./install.sh --target agents
```

Abra uma nova sessão. Se a sua versão do Codex usar outra pasta de skills, use `./install.sh --dest <pasta>`.

## Manus

1. Baixe `dist/video-caricatura-social.zip` deste repositório (ou gere: `cd skills && zip -r ../dist/video-caricatura-social.zip video-caricatura-social`).
2. No Manus, abra a área de Skills/Capacidades e importe o ZIP (ou importe pelo repositório do GitHub,
   se a sua conta oferecer essa opção).
3. Peça: "Crie um vídeo caricatura de 45 segundos sobre ...".

## Claude.ai / aplicativo Claude

Configurações → Capacidades → Skills → enviar `dist/video-caricatura-social.zip`.
(Neste ambiente o script de montagem precisa de execução de código habilitada; sem isso, a skill entrega
roteiro, prompts e legenda, e a montagem pode ser feita em outro ambiente.)

## Windows

```powershell
.\install.ps1                 # Claude Code
.\install.ps1 -Target codex
```

## Verificar

Peça: "Use a skill video-caricatura-social para fazer o plano de um vídeo de 40 s sobre cansaço emocional."
Ela deve conduzir pelo briefing, roteiro e storyboard.

## Atualizar a marca

Edite `brand/brand.json` (dados, CRM, contatos, cores) e troque os PNG em `brand/logos/`. Os nomes das
variantes da marca d'água ficam em `marca_dagua.variantes`.
