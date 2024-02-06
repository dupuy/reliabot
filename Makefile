TARGETS := all checks clean devtools tests uninstall uninstall-pipx update
TOOLS := tox vale
TOOL_DIR := ${HOME}/.local/bin

.PHONY: $(TARGETS) $(TOOLS) $(addprefix has_,$(TOOLS))

ECHO=@echo ""
_:
	@echo Available targets are:
	$(ECHO) $(TARGETS)
	$(ECHO) $(TOOLS)
	$(ECHO)
	$(ECHO) "- $(ALL)"
	$(ECHO) "- $(CHECKS)"
	$(ECHO) "- $(CLEAN)"
	$(ECHO) "- $(DEVTOOLS)"
	$(ECHO) "- $(TESTS)"
	$(ECHO) "- $(UNINSTALL)"
	$(ECHO) "- $(UNINSTALL_PIPX)"
	$(ECHO) "- $(UPDATE)"
	$(ECHO) "- $(TOX)"
	$(ECHO) "- $(VALE)"

ALL= all - Run documentation checks and code tests
all: checks tests

CHECKS= checks - Check documentation style
checks: has_vale $(STYLES)
	vale ./*.md .github/ISSUE_TEMPLATE/*.md

CLEAN= clean - Remove (generated) files ignored by Git
clean:
	git clean -diX

DEVTOOLS= tools - Install all development and documentation tools
devtools: $(TOOLS)

PIPX=${TOOL_DIR}/pipx

TESTS= tests - Run full test suite
tests: has_tox
	tox

$(addprefix has_,${TOOLS}):
	@TOOL_NAME=$(subst has_,,$@); which $(subst has_,,$@) || { \
		echo "'$${TOOL_NAME}' not found in \$$PATH" ; \
		printf "Install '$${TOOL_NAME}' with system (brew, choco, etc.)" ; \
		echo " or by running 'make $${TOOL_NAME}'." ;  exit 1 ; \
	}

PACKAGES = $(shell sed -n 's/Packages *=//p' .vale.ini | tr -d ,)
STYLES = $(addprefix styles/,${PACKAGES})

$(TOOLS): ${TOOL_DIR}/pipx
	${TOOL_DIR}/pipx install --force $@
	@# vale self-downloads on first install
	@case $@ in vale) vale sync || pipx uninstall $@;; esac

${TOOL_DIR}/pipx:
	python3 -m pip install --upgrade --user pip
	python3 -m pip install --upgrade --user certifi pipx
	python3 -m pipx install --force pipx
	yes | python3 -m pip uninstall pipx
	${TOOL_DIR}/pipx ensurepath

TOX= tox - Install tox if necessary

UNINSTALL= uninstall - Uninstall add-on packages
uninstall:
	if [ -x "$(PIPX)" ]; then for T in $(TOOLS); do pipx uninstall $$T; done; fi

UNINSTALL_PIPX= uninstall-pipx - Uninstall pipx and all packages it installed
uninstall-pipx:
	rm -rf $(TOOL_DIR)

UPDATE= update - Update add-on packages
update: has_vale
	vale sync

VALE= vale - Install vale if necessary

$(addprefix %/,${PACKAGES}): %
	${MAKE} sync
