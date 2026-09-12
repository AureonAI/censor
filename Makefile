.PHONY: install test serve avaliar
install:
	pip install -r requirements.txt
test:
	python teste_stj_hc_1094270.py
	python teste_fraude.py
avaliar:
	python gerar_conjunto.py
	python avaliar.py
serve:
	python servico_censor.py
