# Simple HTTP→SOCKS5 proxy bridge using PowerShell
# Usage: Start this script, then set HTTP_PROXY to http://127.0.0.1:10809

$HTTP_PORT = 10809
$SOCKS_PROXY = "127.0.0.1:10808"

Write-Host "Starting HTTP→SOCKS5 bridge on port $HTTP_PORT..." -ForegroundColor Green
Write-Host "Target SOCKS5 proxy: $SOCKS_PROXY" -ForegroundColor Yellow
Write-Host "Set HTTP_PROXY=http://127.0.0.1:$HTTP_PORT" -ForegroundColor Cyan

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$HTTP_PORT/")
$listener.Start()

Write-Host "Proxy bridge running... Press Ctrl+C to stop" -ForegroundColor Green

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        try {
            # Forward request through SOCKS5 proxy
            $webRequest = [System.Net.WebRequest]::Create($request.Url)
            $webRequest.Method = $request.HttpMethod
            $webRequest.Proxy = New-Object System.Net.WebProxy("socks5://$SOCKS_PROXY")

            # Copy headers
            foreach ($key in $request.Headers.AllKeys) {
                if ($key -notin @["Host", "Connection", "Content-Length"]) {
                    $webRequest.Headers[$key] = $request.Headers[$key]
                }
            }

            # Copy body if present
            if ($request.InputStream.CanRead -and $request.ContentLength64 -gt 0) {
                $body = New-Object byte[] $request.ContentLength64
                $request.InputStream.Read($body, 0, $body.Length)
                $webRequest.ContentLength = $body.Length
                $webRequest.GetRequestStream().Write($body, 0, $body.Length)
            }

            # Get response
            $webResponse = $webRequest.GetResponse()
            $responseStream = $webResponse.GetResponseStream()
            $responseStream.CopyTo($response.OutputStream)
            $responseStream.Close()
            $webResponse.Close()
        }
        catch {
            Write-Host "Error: $_" -ForegroundColor Red
            $response.StatusCode = 502
            $response.StatusDescription = "Bad Gateway"
        }
        finally {
            $response.Close()
        }
    }
}
finally {
    $listener.Stop()
    Write-Host "Proxy bridge stopped" -ForegroundColor Yellow
}
