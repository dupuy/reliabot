# Makefile to (re)generata requirements.txt with hashes

requirements.txt: requirements.in Makefile
	pip-compile --generate-hashes --strip-extras > "$@"
