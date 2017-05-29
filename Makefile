# Copyright (C) m-click.aero GmbH
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

.DELETE_ON_ERROR:

.PHONY: usage
usage:
	@echo ''
	@echo 'Usage:'
	@echo ''
	@echo '    make check'
	@echo '    make clean'
	@echo ''

.PHONY: check
check: check2 check3

.PHONY: check2 check3
check2 check3: check%: tmp/lib%.zip
	@PYTHONPATH=$< python$* -B -m pytest -p no:cacheprovider -- tests/

PACKAGES_2 = pytest typing
PACKAGES_3 = pytest

tmp/lib%.zip:
	rm -rf $(basename $@)
	pip$* install --isolated --system -t $(basename $@) $(PACKAGES_$*)
	cd $(basename $@) && zip -r9 ../$(notdir $@) *
	rm -rf $(basename $@)

.PHONY: clean
clean:
	rm -rf tmp/