# Small toolbox image so agents/humans need only Docker: gh, git, jq, ssh, curl.
FROM alpine:3.20
RUN apk add --no-cache github-cli git jq openssh-client curl bash \
 && git config --system --add safe.directory '*'
WORKDIR /repo
