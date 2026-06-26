# MouthClick

O MouthClick é um projeto que eu fiz para testar uma forma diferente de controlar o computador usando só a webcam.

A ideia nasceu como um experimento de acessibilidade: usar o nariz para mover o mouse e usar um gesto com a língua para clicar. Eu comecei esse projeto chamando ele de BlinkClick, porque no começo o clique seria feito com piscadas. Depois de testar melhor, percebi que clicar com a língua fazia mais sentido, porque é um gesto mais intencional e evita cliques sem querer.

Por isso o nome mudou para MouthClick.

Ainda considero o projeto um protótipo, mas ele já consegue mover o mouse real e fazer clique esquerdo real usando a câmera.

## O que ele faz

- Detecta o rosto pela webcam.
- Usa a ponta do nariz para controlar o movimento do mouse.
- Detecta um gesto com a língua para fazer o clique esquerdo.
- Tem uma interface simples com botões para bloquear, centralizar e calibrar.
- Permite ajustar a sensibilidade do movimento.
- Pausa o movimento do mouse enquanto o gesto de clique está acontecendo.
- Salva algumas configurações locais, como sensibilidade e calibração.
- Processa tudo no próprio computador.

## Por que eu fiz

Eu quis criar algo que pudesse servir como base para um sistema de acessibilidade mais completo. A ideia é que uma pessoa consiga usar o computador mesmo sem depender tanto do teclado ou do mouse tradicional.

Também fiz esse projeto para aprender mais sobre visão computacional, MediaPipe, OpenCV e controle de mouse com Python.

## Segurança e privacidade

Como o MouthClick mexe no mouse real, eu tentei tomar alguns cuidados desde o começo:

- existe botão para bloquear e desbloquear o controle real;
- existe botão para sair do programa;
- o PyAutoGUI fica com failsafe ativo;
- existe cooldown entre cliques;
- o clique só acontece quando o rosto está detectado e o sistema está liberado;
- o movimento pausa durante o gesto de clique;
- não implementei clique direito, scroll, arrastar ou duplo clique;
- a imagem da webcam não é salva;
- nenhum dado é enviado para servidor;
- nenhuma API externa é usada.

Tudo é processado localmente.

## Como rodar

Dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

No Windows, também deixei um arquivo para abrir o programa mais fácil:

```text
iniciar_mouthclick.bat
```

## Como eu testo

Normalmente eu testo assim:

1. Abro o programa.
2. Espero ele detectar meu rosto.
3. Clico em `Centralizar nariz`.
4. Ajusto a sensibilidade.
5. Mexo a cabeça devagar para ver se o mouse acompanha.
6. Coloco a língua para fora para testar o clique.
7. Uso `Bloquear mouse real` quando quero parar o controle.

Se o mouse não mexer, geralmente é porque as dependências foram instaladas em outro Python. Nesse caso, eu rodo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Estrutura do projeto

O código principal fica na pasta:

```text
mouthclick/
```

A pasta `blinkclick/` ficou só por compatibilidade com o nome antigo do projeto.

Arquivos principais:

```text
main.py                            entrada principal
mouthclick/src/app.py              loop principal da webcam
mouthclick/src/mouse_controller.py controle real do mouse
mouthclick/src/tongue_detector.py  detecção do gesto de língua
mouthclick/src/visual_cursor.py    movimento e sensibilidade
mouthclick/src/drawing.py          interface desenhada com OpenCV
```

## Testes

Antes de subir alguma mudança, eu costumo rodar:

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py mouthclick\main.py mouthclick\__main__.py blinkclick\main.py mouthclick\src\*.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## O que ainda quero melhorar

O projeto ainda não está finalizado. Algumas coisas que quero melhorar:

- deixar o rastreio do nariz mais estável;
- melhorar a calibração da língua;
- testar em câmeras diferentes;
- deixar a interface mais bonita e mais confortável de usar;
- gerar um executável para Windows;
- testar em outros computadores.

## Licença

O código está sob licença MIT.

O arquivo `models/face_landmarker.task` é usado pelo MediaPipe. Mais detalhes estão em `NOTICE.md`.
