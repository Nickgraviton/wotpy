# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = WoTPy
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -fr _build && rm -fr _autosummary

# Build tags and develop branch. Then write a
# root index.html redirecting to the develop build.
multiversion:
	sphinx-multiversion $(SOURCEDIR) $(BUILDDIR)
	printf '<meta http-equiv="refresh" content="0; url=develop/index.html">\n' > $(BUILDDIR)/index.html

.PHONY: help Makefile clean multiversion

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)