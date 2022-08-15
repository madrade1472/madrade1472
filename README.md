# <p align="left"> Apaixonado por dados, aspirante a engenheiro de dados, Marcus Andrade 👨🏻‍💻 </p>



## Quem sou eu??
- 💻 Analista de Dados / Engenheiro de Dados
- 🎓 Bacharel em Engenharia de Telecomunicações - UNIFIEO.
- 🎓 Tecnologia em Redes de Computadores - Anhanguera.
- 🎓 MBA - Gestão de Projetos - Anhembi Morumbi
- 🎓 Pós Graduação - Engenharia de Dados - Anhembi Morumbi

## Skills - Proficient 💻
- 🐍 Python  
- 📋 SQL 
- 💡 Spark
- 🎡 Airflow
- 🧮 Power BI 
- 🎲 Data Analysis
- ServiceNow
- ZOHO


## Skills em Evolução
- GCP - Google Cloud Plataform
- Azure - Arquiteto
- Airflow


## Conhecimentos em Clouds
- GCP (BigQuery, Cloud Storage)
- Azure (Gen2, Criação de Pipes, Job's, Processos.)
- SQL - (Procedures, Querys, Bkp's)

## Idiomas 🌎
- PT: Nativo
- EN: Avançado
- ES: Básico

 


## Find me  📫
<p align="left">
<a href="https://www.linkedin.com/in/marcus-andrade-b5a2ba101/" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/linked-in-alt.svg" alt="laune-victor/" height="30" width="40" /></a> <a href="https://www.youtube.com/channel/UCgXO6Z43ClpxDmDok4MHwgQ" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/youtube.svg" alt="laune-victor/" height="30" width="40" /></a>
</p>



name: Generate Datas

on:
  schedule: # execute every 12 hours
    - cron: "* */12 * * *"
  workflow_dispatch:

jobs:
  build:
    name: Jobs to update datas
    runs-on: ubuntu-latest
    steps:
      # Snake Animation
      - uses: Platane/snk@master
        id: snake-gif
        with:
          github_user_name: madrade1472
          svg_out_path: dist/github-contribution-grid-snake.svg

      - uses: crazy-max/ghaction-github-pages@v2.1.3
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  
