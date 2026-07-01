.PHONY: ci

# Thin wrapper so `make ci` and `./run_ci.sh` are interchangeable.
# make aborts on the first non-zero recipe line, so the real exit code is preserved.
ci:
	./run_ci.sh
