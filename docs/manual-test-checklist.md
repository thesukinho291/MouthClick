# Checklist de teste manual

Use este checklist antes de publicar uma nova versao.

## Inicializacao

- [ ] `python -m mouthclick --help` mostra ajuda sem abrir a webcam.
- [ ] `python -m mouthclick --version` mostra a versao.
- [ ] `python -m mouthclick` abre a webcam.
- [ ] O app tenta iniciar com mouse real ativo.
- [ ] O botao `Sair` encerra o app.

## Webcam e rosto

- [ ] O rosto e detectado.
- [ ] A malha facial aparece.
- [ ] A ponta do nariz fica destacada.
- [ ] A qualidade fica `boa` quando o rosto esta estavel.
- [ ] A qualidade fica `instavel` com movimento brusco.

## Cursor

- [ ] O botao `Centralizar nariz` recentraliza.
- [ ] Os botoes `-` e `+` ajustam a sensibilidade.
- [ ] A sensibilidade Y aparece sempre 1 acima da X.
- [ ] Ao aumentar a sensibilidade, o mouse real fica mais rapido.
- [ ] Ao diminuir a sensibilidade, o mouse real fica mais lento.
- [ ] O cursor visual acompanha o nariz.
- [ ] O cursor fica mais firme, sem saltos grandes em movimentos pequenos.
- [ ] O mouse real se move com o nariz quando o app esta ativo.
- [ ] O botao `Ativar mouse real` libera o controle se ele estiver bloqueado.
- [ ] Com qualidade boa, o nariz move o mouse real.
- [ ] O botao `Bloquear mouse real` bloqueia novamente.
- [ ] O botao `Sair` encerra com seguranca.

## Calibracao

- [ ] O botao `Calibrar nariz` inicia a calibracao do nariz.
- [ ] As cinco etapas aparecem na tela.
- [ ] A calibracao e salva ao final.
- [ ] O botao `Calibrar lingua` inicia a calibracao da lingua.
- [ ] A fase de boca normal aparece.
- [ ] A fase de lingua aparece.
- [ ] Os novos limites aparecem no diagnostico.

## Clique

- [ ] O clique nao acontece com o sistema bloqueado.
- [ ] O clique nao acontece com qualidade instavel.
- [ ] Com sistema desbloqueado e qualidade boa, o gesto de lingua gera clique esquerdo.
- [ ] Ao mostrar a lingua, o cursor segura posicao em vez de fugir.
- [ ] O cooldown evita cliques repetidos.

## Arquivos locais

- [ ] `mouthclick_settings.json` e criado localmente.
- [ ] `logs\mouthclick.log` e criado localmente.
- [ ] Nenhum dos dois aparece como arquivo rastreado pelo Git.
