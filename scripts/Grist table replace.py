$ErrorActionPreference = 'Stop'

$gristUrl = 'http://127.0.0.1:8484'
$activeDocId = '3TwLJyu7fythPjAj1e1424'
$candidateDocId = 'w1BvHVv8dMpgjevtx5YZu9'

$secureKey = Read-Host 'Grist API key' -AsSecureString
$keyPointer = [IntPtr]::Zero

try {
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)

    $headers = @{
        Authorization = "Bearer $key"
    }

    Write-Host 'Testing Grist authentication...'

    Invoke-RestMethod `
        -Method Get `
        -Uri "$gristUrl/api/orgs" `
        -Headers $headers |
        Out-Null

    Write-Host 'Authentication successful.'

    Write-Host 'Checking candidate document...'

    Invoke-RestMethod `
        -Method Get `
        -Uri "$gristUrl/api/docs/$candidateDocId" `
        -Headers $headers |
        Out-Null

    Write-Host "Candidate document found: $candidateDocId"
    Write-Host "Active document to replace: $activeDocId"

    $confirmation = Read-Host 'Type REPLACE to continue'

    if ($confirmation -cne 'REPLACE') {
        throw 'Replacement cancelled. No document was changed.'
    }

    $body = @{
        sourceDocId = $candidateDocId
    } | ConvertTo-Json -Compress

    Write-Host 'Replacing active document...'

    $result = Invoke-RestMethod `
        -Method Post `
        -Uri "$gristUrl/api/docs/$activeDocId/replace" `
        -Headers $headers `
        -ContentType 'application/json' `
        -Body $body

    Write-Host "Replacement result: $result"
    Write-Host 'Checking Ref_rules in the active document...'

    $rulesResponse = Invoke-RestMethod `
        -Method Get `
        -Uri "$gristUrl/api/docs/$activeDocId/tables/Ref_rules/records" `
        -Headers $headers

    $rules = @($rulesResponse.records)

    $summary = [PSCustomObject]@{
        Total    = $rules.Count
        Critical = @($rules | Where-Object {
            $_.fields.severity -eq 'Critical'
        }).Count
        High     = @($rules | Where-Object {
            $_.fields.severity -eq 'High'
        }).Count
        Medium   = @($rules | Where-Object {
            $_.fields.severity -eq 'Medium'
        }).Count
    }

    $summary | Format-List

    if (
        $summary.Total -ne 143 -or
        $summary.Critical -ne 81 -or
        $summary.High -ne 48 -or
        $summary.Medium -ne 14
    ) {
        throw 'The document was replaced, but rule-count verification failed.'
    }

    Write-Host 'SUCCESS: replacement and rule-count verification passed.' `
        -ForegroundColor Green
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }

    Remove-Variable `
        key, secureKey, keyPointer, headers, body, rulesResponse, rules `
        -ErrorAction SilentlyContinue
}