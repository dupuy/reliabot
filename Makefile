TARGETS := all build clean devtools major minor patch release \
           tests uninstall uninstall-pipx update words
TOOLS := git-cliff poetry tox vale
TOOL_DIR := ${HOME}/.local/bin

.PHONY: $(TARGETS) $(TOOLS) $(addprefix has-,$(TOOLS))

echo=@echo ""
_:
	@echo Available targets are:
	$(echo) $(TARGETS)
	$(echo) $(TOOLS)
	$(echo)
	$(echo) "- $(ALL)"
	$(echo) "- $(BUILD)"
	$(echo) "- $(CLEAN)"
	$(echo) "- $(DEVTOOLS)"
	$(echo) "- $(MAJOR)"
	$(echo) "- $(MINOR)"
	$(echo) "- $(PATCH)"
	$(echo) "- $(TESTS)"
	$(echo) "- $(TOX)"
	$(echo) "- $(UNINSTALL)"
	$(echo) "- $(UNINSTALL_PIPX)"
	$(echo) "- $(UPDATE)"
	$(echo) "- $(VALE)"
	$(echo) "- $(WORDS)"

ALL= all - Run code tests and review word quality of docs, then build package
all: tests words
	$(MAKE) build

BUILD= build - Build Python package
build:
	poetry build -n

CLEAN= clean - Remove (generated) files ignored by Git
clean:
	git clean -diX

DEVTOOLS= tools - Install all development and documentation tools
devtools: $(TOOLS)

MAJOR= major - Generate a major version release branch/PR
MINOR= minor - Generate a minor version release branch/PR
PATCH= patch - Generate a patch version release branch/PR
RELEASE= release - Generate a semantic version release branch/PR
PR_MAKE_TAG=sed -e 's/^/v/' -e 's/a/-alpha./' -e 's/b/-beta./' -e 's/rc/-rc./'
PR_BRANCH=poetry version --short | ${PR_MAKE_TAG}
PR_MAJOR=poetry version --short | sed -n -e '{s/\..*//p;q;}'
major minor patch release: has-git-cliff has-poetry
	git checkout main
	case $@ in \
	  release) \
	    VERSION=`git-cliff -c pyproject.toml --bumped-version | tr -d v` \
	    ;; \
	  *) VERSION=$@ ;; \
	esac; poetry version "$${VERSION}"
	git checkout -b "release-`${PR_BRANCH}`"
	mkdir -p docs
	LAST=`git describe | sed 's/-.*//'` &&                              \
	git-cliff --config=pyproject.toml --tag "`${PR_BRANCH}`" $${LAST}.. \
	  > "docs/changelog-$$$$~" &&                                       \
	sed '/^# C/,/^releases/d' "docs/CHANGELOG-`${PR_MAJOR}`.md"         \
	 >> "docs/changelog-$$$$~" &&                                       \
	mv "docs/changelog-$$$$~" "docs/CHANGELOG-`${PR_MAJOR}`.md"
	git add docs/CHANGELOG-*.md
	-pre-commit run mdformat
	ln -sf "docs/CHANGELOG-`${PR_MAJOR}`.md" CHANGELOG.md
	poetry lock
	git add pyproject.toml CHANGELOG.md docs/CHANGELOG-*.md poetry.lock
	TITLE="chore(release): reliabot `${PR_BRANCH}`";                       \
	SKIP=codespell,markdown-link-check,vale git commit -m "$${TITLE}";     \
	RELEASE="release-`${PR_BRANCH}`";                                      \
	git push --set-upstream origin "$${RELEASE}";                          \
	if which gh >/dev/null 2>&1; then                                      \
	  gh pr create --fill-verbose --title="$${TITLE}";                     \
	else                                                                   \
	  URL=`git config remote.origin.url`;                                  \
	  BASE=`expr $${URL} : '.*github\.com.\(.*\)\.git'`;                   \
	  echo "PR: https://github.com/$${BASE}/compare/$${RELEASE}?expand=1"; \
	fi

PIPX=${TOOL_DIR}/pipx
POETRY= poetry - Install poetry if necessary

$(addprefix has-,${TOOLS}):
	@TOOL_NAME=$(subst has-,,$@); which $(subst has-,,$@) || { \
	  echo "'$${TOOL_NAME}' not found in \$$PATH"; \
	  printf "Install '$${TOOL_NAME}' with system (brew, choco, etc.)"; \
	  echo " or by running 'make $${TOOL_NAME}'.";  exit 1; \
	}


$(TOOLS): ${TOOL_DIR}/pipx
	${TOOL_DIR}/pipx install --force $@
	${TOOL_DIR}/pipx ensurepath
	@# vale self-downloads on first install
	@PATH=$(TOOL_DIR):$$PATH; \
	 case $@ in vale) vale sync || pipx uninstall $@;; esac

${TOOL_DIR}/pipx:
	python3 -m pip install --upgrade --user pip
	python3 -m pip install --upgrade --user certifi pipx
	python3 -m pipx install --force pipx
	yes | python3 -m pip uninstall pipx
	${TOOL_DIR}/pipx ensurepath

TESTS= tests - Run full test suite
tests: has-tox
	tox

TOX= tox - Install tox if necessary

UNINSTALL= uninstall - Uninstall tools and styles
uninstall:
	if [ -x "$(PIPX)" ]; then \
	  for T in $(TOOLS); do   \
	    pipx uninstall $$T;   \
	  done;                   \
	fi
	git clean -i styles

UNINSTALL_PIPX= uninstall-pipx - Uninstall pipx and all tools it installed
uninstall-pipx:
	rm -rf $(TOOL_DIR)

UPDATE= update - Update vale styles
update: has-vale
	vale sync

VALE= vale - Install vale if necessary
VALE_PKGS = $(shell sed -n 's/Packages *=//p' .vale.ini | tr -d ,)
VALE_STYLES = $(addprefix styles/,$(VALE_PKGS))

WORDS= words - Check documentation words for style
words: has-vale $(VALE_STYLES)
	vale ./*.md .github/ISSUE_TEMPLATE/*.md

$(addprefix %/,${PACKAGES}): %
	${MAKE} sync
