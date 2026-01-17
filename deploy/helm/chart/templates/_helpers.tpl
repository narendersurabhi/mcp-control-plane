{{- define "mcp-control-plane.name" -}}
{{ .Chart.Name }}
{{- end -}}

{{- define "mcp-control-plane.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end -}}
