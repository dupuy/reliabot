TARGETS := all build clean devtools major minor patch prerelease release \
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
	$(echo) "- $(PRERELEASE)"
	$(echo) "- $(RELEASE)"
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

DEVTOOLS= devtools - Install all development and documentation tools
devtools: $(TOOLS)

MAJOR= major - Generate a major version release branch/PR
MINOR= minor - Generate a minor version release branch/PR
PATCH= patch - Generate a patch version release branch/PR
PRERELEASE= prerelease - Generate a pre-release branch/PR
RELEASE= release - Generate a semantic version release branch/PR
PR_MAKE_TAG=sed -e 's/^/v/' -e 's/a/-alpha./' -e 's/b/-beta./' -e 's/rc/-rc./'
VERSION_TAG=poetry version --short | $(PR_MAKE_TAG)
MAJOR_VERSION=poetry version --short | sed -n -e '{s/\..*//p;q;}'
COMPARE=https://github.com/dupuy/reliabot/compare
major minor patch prerelease release: has-git-cliff has-poetry
	git checkout main
	@case $@ in                                                           \
	  release)                                                            \
	    VERSION=`git-cliff -c bump.toml --bumped-version | sed 's/-.*//'` \
	    ;;                                                                \
	  *) VERSION=$@ ;;                                                    \
	esac; poetry version "$${VERSION#v}"
	@RELEASE="`$(VERSION_TAG)`" &&                                     \
	CHANGELOG="docs/CHANGELOG-`$(MAJOR_VERSION)`.md" &&                \
	CHANGELOG_TMP="docs/changelog-$$$$~" &&                            \
	LAST=`git describe | sed 's/-.*//'` &&                             \
	git checkout -b "release-$${RELEASE}"; mkdir -p docs &&            \
	git-cliff --config=pyproject.toml --tag "$${RELEASE}" $${LAST}..   \
	  >"$${CHANGELOG_TMP}" &&                                          \
	sed '/^# C/,/^releases/d' "$${CHANGELOG}" >>"$${CHANGELOG_TMP}" && \
	echo "[$${RELEASE#v}]: $(COMPARE)/$${LAST}..$${RELEASE}"           \
	  >>"$${CHANGELOG_TMP}" &&                                         \
	uniq <"$${CHANGELOG_TMP}" >"$${CHANGELOG}" &&                          \
	ln -sf "$${CHANGELOG}" CHANGELOG.md
	git add docs/CHANGELOG-*.md
	-pre-commit run mdformat poetry-lock
	git add pyproject.toml CHANGELOG.md docs/CHANGELOG-*.md poetry.lock
	TITLE="chore(release): reliabot `$(VERSION_TAG)`" &&                   \
	SKIP=codespell,markdown-link-check,vale git commit -m "$${TITLE}" &&   \
	RELEASE="`git branch --show-current`" &&                               \
	git push --set-upstream origin "$${RELEASE}" &&                        \
	if which gh >/dev/null 2>&1; then                                      \
	  gh pr create --fill-verbose --title="$${TITLE}";                     \
	else                                                                   \
	  URL=`git config remote.origin.url` &&                                \
	  BASE=`expr $${URL} : '.*github\.com.\(.*\)\.git'` &&                 \
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
