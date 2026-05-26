TARGETS := all build clean corpus devtools major minor patch \
	    prerelease release tests uninstall uninstall-pipx update words
TOOLS := git-cliff poetry tox vale
TOOL_DIR := $${HOME}/.local/bin

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
	$(echo) "- $(CORPUS)"
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

CORPUS= corpus - update fuzzing corpus
FUZZ=fuzz/corpus/
corpus: $(FUZZ)github.dependabot.yml $(FUZZ)pre-commit-config.yaml \
	$(FUZZ)testdir.configured.github.dependabot.yml \
	$(FUZZ)testdir.github.action.yml
$(FUZZ)github.dependabot.yml: .github/dependabot.yml
	cp $< $@
$(FUZZ)pre-commit-config.yaml: .pre-commit-config.yaml
	cp $< $@
$(FUZZ)testdir.configured.github.dependabot.yml: \
	 testdir/configured/.github/dependabot.yml
	cp $< $@
$(FUZZ)testdir.github.action.yml: testdir/github/action.yml
	cp $< $@

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
	git fetch origin
	git fetch upstream # needed to get tags from primary fork
	git checkout main
	@case $@ in                                                           \
	  release)                                                            \
	    VERSION=`git-cliff -c bump.toml --bumped-version | sed 's/-.*//'` \
	    ;;                                                                \
	  *) VERSION=$@ ;;                                                    \
	esac; poetry version "$${VERSION#v}"
	@RELEASE="`$(VERSION_TAG)`" &&                                     \
	CHANGELOG="docs/CHANGELOG-`$(MAJOR_VERSION)`.md" &&                \
	CHANGELOG_TMP="docs/changelog-$${PPID}~" &&                        \
	NOTES_TMP="docs/notes-$${PPID}~" &&                                \
	LAST=`git describe --always --abbrev=0` &&                         \
	git checkout -b "release-$${RELEASE}"; mkdir -p docs &&            \
	git-cliff --config=pyproject.toml --tag "$${RELEASE}" $${LAST}..   \
	  | uniq >"$${NOTES_TMP}" &&                                       \
	cat "$${NOTES_TMP}" >"$${CHANGELOG_TMP}" &&                        \
	sed '/^# C/,/^releases/d' "$${CHANGELOG}" >>"$${CHANGELOG_TMP}" && \
	mv "$${CHANGELOG_TMP}" "$${CHANGELOG}" &&                          \
	echo "[$${RELEASE#v}]: $(COMPARE)/$${LAST}..$${RELEASE}"           \
	  >>"$${CHANGELOG}" &&                                             \
	ln -sf "$${CHANGELOG}" CHANGELOG.md
	git add docs/CHANGELOG-*.md
	pre-commit run poetry-lock || true
	git add pyproject.toml poetry.lock .pre-commit-config.yaml \
	  CHANGELOG.md docs/CHANGELOG-*.md
	@TITLE="chore(release): reliabot `$(VERSION_TAG)`" &&                \
	NOTES_TMP="docs/notes-$${PPID}~" &&                                  \
	echo "$${TITLE}" > "$${NOTES_TMP}.msg" &&                            \
	sed '/^# /,/^### /d' "$${NOTES_TMP}" >> "$${NOTES_TMP}.msg" &&       \
	SKIP=codespell,markdown-link-check,vale                              \
	  git commit -F "$${NOTES_TMP}.msg" &&                               \
	RELEASE_BRANCH="`git branch --show-current`" &&                      \
	git push --set-upstream origin "$${RELEASE_BRANCH}" &&               \
	if which gh >/dev/null 2>&1; then                                    \
	  gh pr create --title="$${TITLE}" --body-file="$${NOTES_TMP}.msg";  \
	else                                                                 \
	  URL=`git config remote.origin.url` &&                              \
	  BASE=`expr $${URL} : '.*github\.com.\(.*\)\.git'` &&               \
	  echo "PR: https://github.com/$${BASE}/compare/$${RELEASE_BRANCH}"; \
	fi; rm -f "$${NOTES_TMP}" "$${NOTES_TMP}.msg"

PIPX=$(TOOL_DIR)/pipx
POETRY= poetry - Install poetry if necessary

$(addprefix has-,$(TOOLS)):
	@TOOL_NAME=$(subst has-,,$@); which $(subst has-,,$@) || { \
	  echo "'$${TOOL_NAME}' not found in \$$PATH"; \
	  printf "Install '$${TOOL_NAME}' with system (brew, choco, etc.)"; \
	  echo " or by running 'make $${TOOL_NAME}'.";  exit 1; \
	}


$(TOOLS): $(TOOL_DIR)/pipx
	$(TOOL_DIR)/pipx install --force $@
	$(TOOL_DIR)/pipx ensurepath
	@# vale self-downloads on first install
	@PATH=$(TOOL_DIR):$$PATH; \
	 case $@ in vale) vale sync || pipx uninstall $@;; esac

$(TOOL_DIR)/pipx:
	python3 -m pip install --upgrade --user pip
	python3 -m pip install --upgrade --user certifi pipx
	python3 -m pipx install --force pipx
	yes | python3 -m pip uninstall pipx
	$(TOOL_DIR)/pipx ensurepath

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

$(addprefix %/,$(VALE_PKGS)): %
	vale sync
