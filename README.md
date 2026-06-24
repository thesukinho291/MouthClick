# MouthClick

MouthClick e um prototipo de acessibilidade para Windows que permite controlar o mouse usando a webcam.

O cursor e guiado pela posicao do nariz. O clique esquerdo pode ser acionado por um gesto de lingua, com travas de seguranca, qualidade de deteccao e cooldown para reduzir acionamentos acidentais.

O projeto roda localmente: nao envia imagens, nao usa API externa e nao salva frames da camera.

## Recursos

- Deteccao facial com MediaPipe Face Landmarker.
- Malha facial desenhada em tempo real com OpenCV.
- Ponta do nariz destacada e usada como referencia de movimento.
- Cursor visual dentro da janela para acompanhar o controle.
- Movimento real do mouse com PyAutoGUI.
- Clique esquerdo real por gesto de lingua.
- Painel limpo com status principal.
- Modo diagnostico com dados tecnicos.
- Botoes na propria janela para bloquear/desbloquear, ajustar sensibilidade e recentralizar.
- Sensibilidade vertical sempre 1 ponto acima da horizontal.
- Travamento rapido por teclado.

## Seguranca

MouthClick controla o mouse real, entao o uso deve ser feito com atencao.

Protecoes implementadas:

- Botao e tecla `B` bloqueiam ou desbloqueiam controle real e clique real juntos.
- `ESC` desativa o controle real imediatamente; se ja estiver desativado, encerra.
- `Q` encerra o programa.
- PyAutoGUI `FAILSAFE` fica ativo.
- O mouse nao se move sem rosto detectado.
- O mouse nao se move sem referencia do nariz.
- O mouse nao se move quando a qualidade da deteccao esta instavel.
- O clique real so ocorre com sistema desbloqueado, rosto detectado, qualidade boa e gesto confirmado.
- Existe cooldown entre cliques reais.
- Nao ha clique direito, duplo clique, arrastar, scroll, `mouseDown()` ou `mouseUp()`.

Privacidade:

- A webcam e processada localmente.
- O app nao grava fotos ou videos.
- O app nao envia dados para servidores.
- O app nao usa chaves de API.

## Requisitos

- Windows.
- Python instalado.
- Webcam funcionando.
- Permissao de camera liberada no Windows.
- Arquivo `models\face_landmarker.task` presente no projeto.

Dependencias principais:

- OpenCV
- MediaPipe
- PyAutoGUI

## Instalacao

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativacao do ambiente virtual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Como executar

```powershell
python blinkclick\main.py
```

O pacote ainda se chama `blinkclick` internamente para manter compatibilidade com o comando atual. O nome do produto exibido na interface e na documentacao e MouthClick.

## Controles

| Controle | Acao |
| --- | --- |
| `B` | Bloquear ou desbloquear controle real e clique real |
| Botao `Bloquear/Desbloq.` | Mesma acao da tecla `B` |
| `R` | Recentralizar referencia do nariz |
| Botao `Centro` | Recentralizar referencia do nariz |
| `+` | Aumentar sensibilidade |
| `-` | Diminuir sensibilidade |
| Botoes `-` e `+` | Ajustar sensibilidade na tela |
| `D` | Alternar modo diagnostico |
| `C` | Calibrar piscadas, mantido como recurso de teste |
| `ESC` | Desativar controle real ou sair com seguranca |
| `Q` | Sair |

Atalhos avancados:

| Controle | Acao |
| --- | --- |
| `F8` ou `M` | Alternar apenas o movimento real do mouse |
| `F9` | Armar ou desarmar apenas o sistema |

No uso normal, prefira `B`, porque ele bloqueia ou desbloqueia tudo junto.

## Como usar com seguranca

1. Execute o programa.
2. Fique de frente para a webcam.
3. Aguarde o rosto ser detectado e a qualidade ficar boa.
4. Pressione `R` ou clique em `Centro` para recentralizar.
5. Ajuste a sensibilidade com os botoes `-` e `+`.
6. Use `B` para bloquear ou desbloquear o controle.
7. Mova a cabeca devagar para controlar o cursor.
8. Coloque a lingua para fora para acionar o clique esquerdo.
9. Use `B`, `ESC` ou `Q` para parar rapidamente.

## Interface

O modo normal mostra apenas o essencial:

- rosto detectado ou nao;
- gesto de lingua;
- estado do controle real;
- sensibilidade atual;
- botoes principais.

O modo diagnostico (`D`) mostra valores tecnicos para ajuste:

- abertura dos olhos;
- limite de piscada;
- coordenadas do cursor;
- sensibilidade X/Y;
- suavizacao;
- qualidade da deteccao;
- mensagens de bloqueio;
- cooldown de clique.

## Estrutura do projeto

```text
blinkclick/
  __init__.py
  main.py
  src/
    __init__.py
    app.py
    blink_detector.py
    config.py
    detection_quality.py
    drawing.py
    face_landmarker.py
    mouse_controller.py
    nose_tracker.py
    safety_state.py
    tongue_detector.py
    ui_state.py
    visual_cursor.py
models/
  face_landmarker.task
.gitignore
README.md
requirements.txt
```

Responsabilidades principais:

- `blinkclick/main.py`: ponto de entrada.
- `blinkclick/src/app.py`: loop da webcam e integracao dos modulos.
- `blinkclick/src/face_landmarker.py`: carregamento do modelo local do MediaPipe.
- `blinkclick/src/nose_tracker.py`: leitura da ponta do nariz e centralizacao.
- `blinkclick/src/visual_cursor.py`: cursor visual, suavizacao e sensibilidade.
- `blinkclick/src/mouse_controller.py`: unico arquivo que usa PyAutoGUI.
- `blinkclick/src/tongue_detector.py`: deteccao do gesto de lingua.
- `blinkclick/src/detection_quality.py`: regras simples de estabilidade.
- `blinkclick/src/drawing.py`: interface desenhada com OpenCV.

## Verificacoes antes de publicar

Comandos usados para validar o projeto:

```powershell
python -m py_compile blinkclick\main.py
python -m py_compile blinkclick\src\*.py
```

Tambem e recomendado procurar por arquivos sensiveis antes de subir:

```powershell
rg -n -i "token|secret|password|api_key|ghp_|github_pat|sk-" .
```

## Problemas comuns

### A camera nao abre

- Feche outros aplicativos que estejam usando a webcam.
- Confira as permissoes de camera do Windows.
- Teste a webcam em outro aplicativo.

### O rosto nao e detectado

- Melhore a iluminacao.
- Fique de frente para a camera.
- Evite cobrir o rosto.
- Ajuste a distancia ate a webcam.

### O cursor treme

- Diminua a sensibilidade.
- Recentralize com `R` ou `Centro`.
- Melhore a iluminacao.
- Evite movimentos bruscos.

### O mouse nao se move

- Confira se o sistema esta desbloqueado.
- Confira se a qualidade esta boa.
- Recentralize a referencia do nariz.
- Verifique se PyAutoGUI foi instalado pelo `requirements.txt`.

### O clique nao acontece

- Confira se o sistema esta desbloqueado.
- Confira se a qualidade esta boa.
- Veja o motivo de bloqueio no modo diagnostico.
- Aguarde o cooldown terminar.
- Teste o gesto de lingua com boa iluminacao.

## Limitacoes

- A deteccao de lingua e heuristica: usa abertura da boca e cor na regiao da boca.
- Iluminacao ruim, camera fraca ou sombras podem prejudicar a deteccao.
- Reflexos, barba, maquiagem ou baixa resolucao podem alterar os resultados.
- Movimentos bruscos podem colocar o sistema em qualidade instavel.
- O projeto ainda nao tem instalador nem executavel.
- Ainda nao ha testes automatizados.

## Status

MouthClick esta em fase de prototipo funcional. O foco atual e estabilidade, seguranca e usabilidade antes de qualquer empacotamento para uso diario.
