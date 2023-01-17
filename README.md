# AWS-Experiments-Lambda-Multithreading
AWS Experiments :: Lambda Multithreading

This repo contains code (infra + app) for my Lambda Multithreading experiment.

**If you aren't interested in delving too deep, here's the bottomline so far:**

![Results_BothArchs](https://user-images.githubusercontent.com/24997018/212846707-e0920aeb-7471-4458-84b6-77a57111556a.png)
The rows highlighted in blue show what I found to be the point where the memory size config gave the Lambda instance max performance for a particular number of threads:
- One thread = 2048MB 
- Two threads = 4096MB 
- Three threads = 5376MB
- Four threads = 7168MB
- Five threads = 8960MB
- Six threads = 10240MB (Lambda max memory size)

You can probably get by with slightly less at each point. My experiment jumped by 256MB increments (after testing both 128MB and 256MB configurations), so the granularity of data is mostly in 256MB increments, starting with 128MB, 256MB, 512MB, and so on until reaching 10240MB.

**If you are interested in delving deeper into the raw data:**

Go to the **RESULTS** folder.
Inside that folder, here's what you can find:
- 492 individual CSV files, with the naming convention *"Lambda\_[memorySizeInMB]\_[numThreads]\_[arch].csv"*. 
- For example, for the results of the Lambda instance that has 128MB of RAM, used only 1 worker thread, and ran on the arm64 architecture, it will be found in the "Lambda_128_1_arm64.csv" file.
- Each individual CSV file will have 190 result rows (not counting the header), because each Lambda in this experiment executed 190 times.
- There is a CSV file called *AggregatedResults.csv*, which contain 492 result rows (not counting the header) - exactly one result row per unique Lambda. The average processing time (for all 190 runs) of each of the unique 492 Lambdas are computed and stored in this aggregated CSV file
- Finally, there is a spreadsheet named *AggregatedResults.ods* that is based from the CSV file of the same name. The interesting sheet inside it is called "scratch_finding_max_cores", where a more summarized version of the results can be found that shows the performance scaling of multithreading for different numbers of workers (i.e., finding the minimum memory size that makes X number of worker threads most efficient)

