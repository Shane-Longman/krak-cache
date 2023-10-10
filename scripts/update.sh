#!/bin/bash

## [shellcheck]

set -euxo pipefail

echo ::group::Download yesterday\'s data

if [[ -p /dev/stdin ]]
then
    PAIRS=$(cat -)
    YMD=${1:-$(date -d yesterday +%Y/%m/%d)}
    YM=${YMD:0:7}

    for p in $PAIRS; do

        mkdir -p "${p}/${YM}"
        scripts/scrape_lhoc.py "${p}/${YMD}" "${YMD//\//-}" "${p}"

        # compress and delete original
        xz -9f "${p}/${YMD}"

        sleep 1

    done

else

    echo "[!] Input must be piped in for it to be processed"
    exit 1;

fi


[ -z "${INPUT_GITHUB_TOKEN}" ] && {
    echo 'Missing input "github_token: ${{ secrets.GITHUB_TOKEN }}".';
    exit 1;
};

git remote -v

# get author
author_name="$(git show --format=%an -s)"
author_email="$(git show --format=%ae -s)"

# outputs
echo "::set-output name=name::"$author_name""
echo "::set-output name=email::"$author_email""

# git config
echo ::group::Set commiter
echo "git config user.name \"$author_name\""
git config user.name "$author_name"
echo "git config user.email $author_email"
git config user.email $author_email
echo ::endgroup::

# commit and push
echo ::group::Push
echo "git add ."
git add .
echo 'git commit --allow-empty -m "$YMD"'
git commit --allow-empty -m "${YMD}"
echo "git push origin HEAD"
git push origin HEAD
echo ::endgroup::
