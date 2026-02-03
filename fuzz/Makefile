# Makefile to (re)generata requirements.txt with hashes

requirements.txt: requirements.in Makefile
	pip-compile --strip-extras --generate-hashes > "$@"
