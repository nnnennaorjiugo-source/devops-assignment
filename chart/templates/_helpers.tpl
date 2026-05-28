{{- define "flask-app.labels" -}}
app.kubernetes.io/name: flask-app
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "flask-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- printf "%s-flask-app" .Release.Name }}
{{- else }}
{{- "default" }}
{{- end }}
{{- end }}
