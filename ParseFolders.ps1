#########################
##SCRIPT CONFIG SECTION##
#########################

# this flag allows us to skip hidden files
$checkHiddenFiles = $true
# this settings lets us configure what file extensions to skip, default blank looks at all file types
# TODO: build configuration at the config file level where each set of SLAs can have its own flags, vs at the global level right now
$skipExtensions = ""
# API URI
$API_URI = "https://reqres.in/api/errorFolder"

################
##CODE SECTION##
################

# config properties
# ----------
# DefaultPath = root folder
# Folders = list of folders under root folder to scan
# SLA_List = folder name : time in minutes, folder name must be in the Folders list
$config = Get-Content .\Config.json -Raw | ConvertFrom-json

# keep track of all failed items in all folders
$all_failed_items_list = New-Object System.Collections.ArrayList

foreach($SLA_Item in $config.SLA_Folders_List) {
    $path = Join-Path -Path $config.RootPath -ChildPath $SLA_Item.FolderName
    # build our args based on config section above and use splatting to send to cmdlet
    $HashArguments = @{
        Path = $path
        Force = $checkHiddenFiles
        # exclude needs to be an array to be processed correctly via splatting
        Exclude = $skipExtensions.split(",")
        # TODO: how do we deal with nested folders? full path to file?
        Recurse = $true
    }

    if(Test-Path -Path $path) {
        # we're looking at less than or equal to the x minute old
        $failed_in_path = Get-ChildItem @HashArguments | Select-Object Name, CreationTime | Where-Object { $_.CreationTime -le (Get-Date).AddMinutes(($SLA_Item.SLA_In_Minutes * -1)) }
        # go through the list of failed items and start to build our request JSON obj
        if($failed_in_path) {
            # list to keep track of failed items in this folder
            $failed_in_path_list = New-Object System.Collections.ArrayList
            # record failed items to $failed_in_path_list
            foreach($failed_item in $failed_in_path) {
                $failed_item_object = [PSCustomObject]@{
                    filename     = $failed_item.Name
                    creationDate = $failed_item.CreationTime | Get-Date -f "yyyy-MM-dd HH:mm:ss"
                }
                # need to cast to void here or it will return index when adding
                [void]$failed_in_path_list.Add($failed_item_object)

                # DEBUG
                # Write-Host $failed_in_path_list
            }

            # DEBUG
            # Write-Host $failed_in_path_list

            # bind the data to custom object and add it to the list of all failed items in all folders
            $all_failed_items_in_folder = [PSCustomObject]@{
                folder = $path
                sla = $SLA_Item.SLA_In_Minutes
                files = $failed_in_path_list
            }

            # DEBUG
            # Write-Host $all_failed_items_in_folder

            [void]$all_failed_items_list.Add($all_failed_items_in_folder)
            # Write-Host $all_failed_items_list | Format-Table -AutoSize
        }
    }
    else {
        # TODO: implement logic for if folder doesn't exist, or just skip
        Write-Host ($path + " does not exist.")
    }
}

# DEBUG
# Write-Host $all_failed_items_list

if($all_failed_items_list.Count -gt 0) {
    $jsonObj = @{}
    $jsonObj.Add("sla_error", $all_failed_items_list)
    # build request body with json
    $requestBody = $jsonObj | ConvertTo-Json -Depth 5
    $Params = @{
        Method = "Post"
        Uri = $API_URI
        Body = $requestBody
        ContentType = "application/json"
    }

    try {
        # POST to API
        $response = Invoke-RestMethod @Params
        # perform logic with response depending on code, etc..
        Write-Host $response

        # we are generating a local version of the json to mock sending to lambda
        $response | ConvertTo-Json -dept 5 | Out-File ".\response.json"
    }
    catch {
        # TODO: implement logic for dealing with different errors
        Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__ 
        Write-Host "StatusDescription:" $_.Exception.Response.StatusDescription
    }

    # TODO: authenticate to AWS and store the formatted response in an S3 bucket which will be consumed and stored into DynamoDb
}
# TODO: what logic needs to be implemented if there are no failed slas in this scan? Do we remove existing .json output?