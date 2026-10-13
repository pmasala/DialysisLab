Traceback (most recent call last):
  File "/home/runner/work/DialysisLab/DialysisLab/tools/dependency_report.py", line 179, in <module>
    if __name__=='__main__':main()
                            ^^^^^^
  File "/home/runner/work/DialysisLab/DialysisLab/tools/dependency_report.py", line 138, in main
    data=check(ROOT);identity=build_identity(args.build_dir);expected=source_hashes(ROOT)
         ^^^^^^^^^^^
  File "/home/runner/work/DialysisLab/DialysisLab/tools/dependency_report.py", line 55, in check
    if digest(root/name)!=expected: raise ValueError('reviewed dependency file changed: '+name)
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: reviewed dependency file changed: .github/workflows/verify.yaml
