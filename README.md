# MouthClick

MouthClick e um prototipo de acessibilidade para Windows que controla o mouse usando a webcam.

O movimento do cursor vem da ponta do nariz. O clique esquerdo pode ser acionado com um gesto de lingua. A ideia e permitir uma forma alternativa de interacao para pessoas que precisam ou preferem controlar o computador sem usar as maos.

O app roda localmente. Ele nao envia imagens, nao salva frames da camera e nao usa API externa.

## Estado atual

O projeto ja possui:

- deteccao facial com MediaPipe Face Landmarker;
- malha facial em tempo real com OpenCV;
- controle do cursor pelo nariz;
- clique esquerdo por gesto de lingua;
- pausa automatica do cursor durante o gesto de lingua;
- botao unico para bloquear/desbloquear controle real e clique real;
- botao para sair do programa;
- ajuste de sensibilidade na tela;
- sensibilidade aplicada ao cursor visual e ao movimento real do mouse;
- sensibilidade Y sempre 1 ponto acima da sensibilidade X;
- recentralizacao do nariz;
- calibracao direcional do nariz;
- calibracao do gesto de lingua;
- modo diagnostico;
- configuracoes locais salvas;
- log local de eventos, sem imagens;
- testes unitarios;
- workflow de CI;
- script e spec para gerar executavel com PyInstaller.

## Seguranca

MouthClick pode mover e clicar com o mouse real. Ao abrir, ele tenta deixar o mouse real ativo para seguir a ideia principal do projeto. Use o botao `Bloquear mouse real` para pausar tudo rapidamente.

Protecoes principais:

- O botao `Ativar/Bloquear mouse real` controla movimento real e clique real juntos.
- O botao `Sair` encerra o app.
- `ESC` continua existindo como emergencia para desativar o controle real.
- PyAutoGUI `FAILSAFE` fica ativo.
- O mouse nao se move sem rosto detectado.
- O mouse nao se move sem referencia do nariz.
- O mouse nao se move com deteccao instavel.
- O mouse pausa enquanto a boca/lingua indica intencao de clique.
- O clique real exige sistema desbloqueado, qualidade boa e gesto confirmado.
- Ha cooldown entre cliques.
- Nao existe clique direito, duplo clique, arrastar, scroll, `mouseDown()` ou `mouseUp()`.

Privacidade:

- a webcam e processada localmente;
- nenhuma imagem e gravada;
- nenhum dado e enviado para servidores;
- nao ha chaves de API no projeto.

## Requisitos

- Windows.
- Python 3.11 ou superior.
- Webcam funcionando.
- Permissao de camera liberada no Windows.
- Arquivo `models\face_landmarker.task` dentro do projeto.

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

Comando recomendado, dentro da pasta do projeto:

```powershell
python main.py
```

Tambem da para abrir pelo arquivo:

```text
iniciar_mouthclick.bat
```

Comando por modulo:

```powershell
python -m mouthclick
```

Comando antigo, mantido por compatibilidade:

```powershell
python blinkclick\main.py
```

## Primeiro uso

1. Execute o app.
2. Fique de frente para a webcam.
3. Espere o rosto ser detectado.
4. Clique em `Centro` ou pressione `R`.
5. Ajuste a sensibilidade com `-` e `+`.
6. Calibre o nariz com `N`, se quiser um controle mais preciso.
7. Calibre a lingua com `T`, se o clique estiver falhando ou sensivel demais.
8. Se o app abrir bloqueado, clique em `Ativar mouse real`.
9. Clique em `Bloquear mouse real` ou `Sair` para parar.

## Controles da interface

| Botao | Acao |
| --- | --- |
| `Ativar/Bloquear mouse real` | Bloquear ou liberar movimento real e clique real |
| `Centralizar nariz` | Recentralizar a referencia do nariz |
| `Calibrar nariz` | Iniciar/capturar calibracao direcional do nariz |
| `Calibrar lingua` | Calibrar gesto de lingua |
| `Modo diagnostico` | Mostrar ou ocultar valores tecnicos |
| `-` | Diminuir sensibilidade |
| `+` | Aumentar sensibilidade |
| `Sair` | Encerrar o programa |

O teclado fica apenas como emergencia e compatibilidade. O uso normal deve ser pelos botoes da interface.

## Calibracao do nariz

A calibracao do nariz melhora o mapeamento do movimento da cabeca para a tela.

Pressione `N` para iniciar. Depois siga as mensagens na tela e pressione `N` em cada posicao:

1. centro;
2. esquerda;
3. direita;
4. cima;
5. baixo.

Quando a calibracao termina, ela e salva em `mouthclick_settings.json`. Esse arquivo e local e nao entra no Git.

## Calibracao da lingua

Pressione `T` para calibrar o gesto de clique.

O app coleta duas fases:

1. boca normal;
2. lingua para fora.

Depois disso, ele calcula limites personalizados de abertura da boca e cor da regiao da boca. A calibracao ajuda quando o clique fica sensivel demais ou dificil de acionar.

## Configuracoes locais

O app salva preferencias em:

```text
mouthclick_settings.json
```

Esse arquivo pode guardar:

- sensibilidade;
- modo diagnostico ligado/desligado;
- limite de piscada;
- limites calibrados da lingua;
- calibracao direcional do nariz.

Ele esta no `.gitignore` porque e uma configuracao da maquina local.

## Logs

Eventos simples sao gravados em:

```text
logs\mouthclick.log
```

O log registra eventos como inicio do app, bloqueio, desbloqueio, calibracao e encerramento. Ele nao salva imagem, video nem dados da webcam.

## Estrutura

```text
mouthclick/
  __init__.py
  __main__.py
  main.py
  src/
    app.py
    blink_detector.py
    config.py
    cursor_calibration.py
    detection_quality.py
    drawing.py
    event_log.py
    face_landmarker.py
    mouse_controller.py
    nose_tracker.py
    safety_state.py
    settings.py
    tongue_detector.py
    ui_state.py
    visual_cursor.py
blinkclick/
  __init__.py
  main.py
models/
  face_landmarker.task
tests/
.github/workflows/ci.yml
```

`blinkclick/` existe apenas como compatibilidade com o caminho antigo. O desenvolvimento principal fica em `mouthclick/`.

## Testes

Compilar os arquivos:

```powershell
python -m py_compile mouthclick\main.py mouthclick\__main__.py blinkclick\main.py mouthclick\src\*.py
```

Rodar testes:

```powershell
python -m unittest discover -s tests
```

## Gerar executavel

Instale as dependencias de desenvolvimento e rode:

```powershell
.\build_exe.ps1
```

O script usa PyInstaller e inclui o modelo `models\face_landmarker.task` no build.

## Problemas comuns

### A camera nao abre

- Feche outros apps que usam webcam.
- Confira as permissoes de camera do Windows.
- Teste a camera em outro aplicativo.

### O cursor nao se move

- Confira se o sistema esta desbloqueado.
- Pressione `R` ou clique em `Centro`.
- Espere a qualidade ficar boa.
- Diminua a sensibilidade se houver muita tremedeira.
- Se a lingua ou boca estiverem no gesto de clique, o cursor pausa de proposito.

### O cursor fica solto ou tremendo

- Diminua a sensibilidade com `-`.
- Pressione `R` ou clique em `Centro`.
- Use a calibracao do nariz com `N`.
- Melhore a iluminacao e evite movimentos bruscos.
- Durante o gesto de lingua, o cursor deve ficar parado no ultimo ponto estavel.

### O clique nao acontece

- Confirme se o sistema esta desbloqueado.
- Ative o diagnostico com `D` e veja o motivo de bloqueio.
- Calibre a lingua com `T`.
- Melhore a iluminacao.
- Aguarde o cooldown terminar.

### O clique acontece facil demais

- Calibre a lingua com `T`.
- Evite sombras fortes na boca.
- Use o app com iluminacao frontal.

## Limitacoes

- A deteccao de lingua ainda e heuristica.
- Iluminacao ruim pode afetar boca, nariz e malha facial.
- Cameras de baixa resolucao podem gerar instabilidade.
- O projeto ainda nao tem instalador assinado.
- O executavel ainda precisa ser testado em maquinas diferentes.

## Licenca

O codigo do MouthClick esta sob licenca MIT. Veja `LICENSE`.

O modelo `models/face_landmarker.task` e um ativo de terceiros usado pelo MediaPipe. Veja `NOTICE.md`.
