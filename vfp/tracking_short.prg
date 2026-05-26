* tracking_short.prg
* Funcion VFP para generar URL de tracking corta.
* Flujo:
* 1) POST /api/track-token/
* 2) GET  /api/track-preview/?t=... (no registra apertura)
* 3) POST /api/track-shorten/
* 4) Fallback a /api/track/?t=... si falla el acortador

FUNCTION JsonEscape(tcText)
    LOCAL lc
    lc = IIF(VARTYPE(tcText) = 'C', tcText, TRANSFORM(tcText))
    lc = STRTRAN(lc, '\\', '\\\\')
    lc = STRTRAN(lc, '"', '\\"')
    lc = STRTRAN(lc, CHR(13), '\\r')
    lc = STRTRAN(lc, CHR(10), '\\n')
    RETURN lc
ENDFUNC

FUNCTION UrlEncodeToken(tcToken)
    LOCAL lc
    lc = ALLTRIM(tcToken)
    lc = STRTRAN(lc, '+', '%2B')
    lc = STRTRAN(lc, '/', '%2F')
    lc = STRTRAN(lc, '=', '%3D')
    RETURN lc
ENDFUNC

FUNCTION NormalizeShortUrl(tcUrl, tcBaseUrl)
    LOCAL lc
    lc = ALLTRIM(tcUrl)

    IF EMPTY(lc)
        RETURN ''
    ENDIF

    * Si llega relativa, la volvemos absoluta
    IF LEFT(lc, 7) = '/api/t/'
        RETURN ALLTRIM(tcBaseUrl) + lc
    ENDIF

    IF LEFT(lc, 3) = '/t/'
        RETURN ALLTRIM(tcBaseUrl) + '/api' + lc
    ENDIF

    * Compatibilidad: si el backend devuelve /t/ en raiz, forzamos /api/t/
    lc = STRTRAN(lc, 'https://ventas.ferreteriaavenida.com.ar/t/', 'https://ventas.ferreteriaavenida.com.ar/api/t/')
    lc = STRTRAN(lc, 'http://ventas.ferreteriaavenida.com.ar/t/', 'http://ventas.ferreteriaavenida.com.ar/api/t/')

    RETURN lc
ENDFUNC

FUNCTION GetTrackUrl(tcEmail, tcCampaign, tcTargetUrl)
    LOCAL loHttp, loEx
    LOCAL lcBody, lcResp, lcToken, lcTokenEncoded
    LOCAL lcTrackUrl, lcPreviewUrl, lcShortBody, lcShortResp

    * Endpoints
    LOCAL lcBaseUrl, lcTokenUrl, lcPreviewBase, lcShortenUrl, lcTrackBase
    lcBaseUrl = 'https://ventas.ferreteriaavenida.com.ar'
    lcTokenUrl = lcBaseUrl + '/api/track-token/'
    lcPreviewBase = lcBaseUrl + '/api/track-preview/?t='
    lcShortenUrl = lcBaseUrl + '/api/track-shorten/'
    lcTrackBase = lcBaseUrl + '/api/track/?t='

    * Armar payload JSON para generar token
    lcBody = '{"email":"' + JsonEscape(ALLTRIM(tcEmail)) + '","campaign":"' + JsonEscape(ALLTRIM(tcCampaign)) + '","url":"' + JsonEscape(ALLTRIM(tcTargetUrl)) + '"}'

    loHttp = CREATEOBJECT('MSXML2.ServerXMLHTTP')

    * 1) Pedir token
    TRY
        loHttp.setTimeouts(5000, 5000, 15000, 15000)
        loHttp.open('POST', lcTokenUrl, .F.)
        loHttp.setRequestHeader('Content-Type', 'application/json')
        loHttp.send(lcBody)
    CATCH TO loEx
        MESSAGEBOX('Error HTTP al pedir token: ' + loEx.Message)
        RETURN ''
    ENDTRY

    IF loHttp.status <> 200
        MESSAGEBOX('Error HTTP al pedir token: ' + TRANSFORM(loHttp.status) + ' - ' + loHttp.statusText)
        RETURN ''
    ENDIF

    lcResp = ALLTRIM(loHttp.responseText)
    IF EMPTY(lcResp)
        MESSAGEBOX('Respuesta vacia del servidor (token)')
        RETURN ''
    ENDIF

    lcToken = lcResp
    lcTokenEncoded = UrlEncodeToken(lcToken)

    * 2) Validar payload por preview (no bloqueante)
    lcPreviewUrl = lcPreviewBase + lcTokenEncoded
    TRY
        loHttp.open('GET', lcPreviewUrl, .F.)
        loHttp.setRequestHeader('Accept', 'application/json')
        loHttp.send()

        IF loHttp.status <> 200
            MESSAGEBOX('Advertencia: preview devolvio HTTP ' + TRANSFORM(loHttp.status))
        ELSE
            lcResp = ALLTRIM(loHttp.responseText)
            IF !EMPTY(ALLTRIM(tcTargetUrl)) AND AT(ALLTRIM(tcTargetUrl), lcResp) = 0
                MESSAGEBOX('Advertencia: el preview no devolvio la URL esperada')
            ENDIF
        ENDIF
    CATCH TO loEx
        MESSAGEBOX('Advertencia: no se pudo validar el token (preview): ' + loEx.Message)
    ENDTRY

    * 3) Pedir URL corta enviando token
    lcShortBody = '{"token":"' + JsonEscape(lcToken) + '"}'

    TRY
        loHttp.open('POST', lcShortenUrl, .F.)
        loHttp.setRequestHeader('Content-Type', 'application/json')
        loHttp.send(lcShortBody)
    CATCH TO loEx
        * Fallback a link largo
        lcTrackUrl = lcTrackBase + lcTokenEncoded
        RETURN lcTrackUrl
    ENDTRY

    IF loHttp.status = 200
        lcShortResp = ALLTRIM(loHttp.responseText)
        IF !EMPTY(lcShortResp) AND 'http' $ LOWER(lcShortResp)
            lcShortResp = NormalizeShortUrl(lcShortResp, lcBaseUrl)
            RETURN lcShortResp
        ENDIF
    ENDIF

    * 4) Fallback final: link largo
    lcTrackUrl = lcTrackBase + lcTokenEncoded
    RETURN lcTrackUrl
ENDFUNC
