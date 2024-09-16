#!/usr/bin/env sh

main() {
  if [ "$1" = 'mumbleice' ] && [ "$(id -u)" = '0' ]; then
    exec gosu mumbleice "$@"
  fi

  exec "$@"
}

main "$@"
