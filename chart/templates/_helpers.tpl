{{- define "flask-app.labels" -}}
app.kubernetes.io/name: flask-app
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
