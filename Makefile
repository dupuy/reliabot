DIR = styles
PACKAGES = $(shell sed -n 's/Packages *=//p' .vale.ini | tr -d ,)
STYLES = $(addprefix ${DIR}/,${PACKAGES})

checks: vale

clean:
	git clean -fX ${DIR}

vale: ${STYLES}
	vale *.md

sync:
	vale sync

$(addprefix %/,${PACKAGES}): %
	${MAKE} sync

.PHONY: checks clean vale sync
