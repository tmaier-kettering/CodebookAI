# Frequently Asked Questions (FAQ)

Quick answers to the most common questions about CodebookAI. For detailed troubleshooting, see the [Troubleshooting Guide](Troubleshooting.md).

## 🚀 Getting Started

### Q: What is CodebookAI and who is it for?
**A:** CodebookAI is a qualitative research tool that uses OpenAI's GPT models to automate text classification tasks. It's designed for researchers, analysts, and anyone who needs to categorize large amounts of text data efficiently and cost-effectively.

### Q: Do I need programming experience to use CodebookAI?
**A:** No! CodebookAI is designed with a user-friendly graphical interface. You work with familiar file formats (CSV, Excel) and use wizard-based workflows. No coding required.

### Q: How much does it cost to use CodebookAI?
**A:** CodebookAI itself is free and open-source. However, you need an OpenAI API account, which charges based on usage. Costs typically range from $0.50-$5.00 per 1,000 text snippets, depending on the model and text length.

### Q: What types of text can CodebookAI analyze?
**A:** CodebookAI can analyze any text data including:
- Survey responses and interview transcripts
- Social media posts and comments
- News articles and press releases
- Customer reviews and feedback
- Academic papers and documents
- Email content and support tickets

---

## 💰 Cost and Pricing

### Q: How much will my project cost?
**A:** Costs depend on several factors:
- **Model choice**: gpt-4o-mini (~$0.15/1K tokens) vs gpt-4o (~$2.50/1K tokens)
- **Text length**: Longer texts cost more
- **Processing method**: Batch processing offers ~50% savings
- **Example**: 1,000 short reviews with gpt-4o-mini in batch mode ≈ $0.75

### Q: What's the difference between Live and Batch processing costs?
**A:** 
- **Live Processing**: Standard API rates, immediate results
- **Batch Processing**: Up to 50% discount, 2-24 hour processing time
- **Recommendation**: Use Live for testing (<100 items), Batch for production (500+ items)

### Q: How can I minimize costs?
**A:**
1. **Start with gpt-4o-mini**: Test with the cheapest model first
2. **Use Batch Processing**: Significant savings for large datasets
3. **Clean your text**: Remove unnecessary content to reduce token count
4. **Test small samples**: Validate your approach before processing everything
5. **Choose efficient labels**: Clear, unambiguous labels reduce processing complexity

### Q: Can I set spending limits?
**A:** Yes, through your OpenAI account dashboard. Set monthly spending limits and usage alerts to control costs.

---

## 🔧 Technical Questions

### Q: What file formats does CodebookAI support?
**A:** 
- **Input**: CSV, TSV, TXT (delimited), Excel (.xlsx, .xls, .xlsm)
- **Output**: CSV, Excel with multiple sheets for analysis results
- **Encoding**: Automatic UTF-8 detection and conversion

### Q: How large can my datasets be?
**A:**
- **File size**: Up to ~100MB per file
- **Number of items**: No hard limit, but consider costs and processing time
- **Recommendation**: For >10,000 items, consider splitting into multiple batches
- **Memory**: Depends on your system RAM; large datasets may require more memory

### Q: Which OpenAI models should I use?
**A:**
- **gpt-4o-mini**: Best for cost-conscious projects, simple classifications
- **gpt-4o**: Balanced cost and quality, recommended for most projects
- **gpt-4-turbo**: Highest quality for complex or nuanced classifications
- **o1-preview**: Advanced reasoning tasks (limited availability)

### Q: Can I use CodebookAI offline?
**A:** No, CodebookAI requires internet connection to communicate with OpenAI's API. However, your data is processed securely and not stored by OpenAI.

---

## 📊 Data and Results

### Q: How accurate are the AI classifications?
**A:** Accuracy varies by:
- **Model choice**: Better models = higher accuracy
- **Label quality**: Clear, distinct labels improve accuracy
- **Text quality**: Clean, well-written text classifies better
- **Typical range**: 80-95% accuracy with well-designed label sets
- **Validation**: Always validate results with human review of samples

### Q: Can I compare AI results with human coding?
**A:** Yes! Use the **Reliability Statistics** feature to:
- Calculate Cohen's Kappa and percentage agreement
- Compare AI vs human classifications
- Generate detailed statistical reports
- Export results for further analysis

### Q: What if the AI makes mistakes?
**A:**
1. **Sample validation**: Always review a sample of results
2. **Refine labels**: Unclear labels lead to more errors
3. **Try different model**: Higher-end models may be more accurate
4. **Iterate**: Use results to improve your approach
5. **Combine approaches**: Use AI for initial classification, human review for quality control

### Q: Can I classify text with multiple labels?
**A:** Yes! CodebookAI supports both:
- **Single Label**: Each text gets exactly one label
- **Multi-Label**: Each text can have multiple relevant labels
- Use Multi-Label for complex categorization where texts may fit multiple categories

---

## 🔄 Processing and Workflow

### Q: How long does processing take?
**A:**
- **Live Processing**: 5-30 minutes for 100 items (depends on model and text length)
- **Batch Processing**: 2-24 hours (usually 4-8 hours for typical jobs)
- **Factors**: Model choice, OpenAI system load, text complexity, dataset size

### Q: Can I stop processing once it's started?
**A:**
- **Live Processing**: Yes, you can cancel anytime
- **Batch Processing**: You can cancel jobs while in queue, but not once processing starts
- **Partial Results**: Live processing saves completed items even if cancelled

### Q: What happens if processing fails?
**A:**
- **Automatic Retries**: Failed requests are automatically retried
- **Error Reporting**: Detailed error logs for troubleshooting
- **Partial Success**: Successfully processed items are saved
- **Recovery**: You can reprocess failed items separately

### Q: Can I process data in languages other than English?
**A:** Yes! OpenAI models support many languages. However:
- **Performance varies**: Some languages work better than others
- **Label language**: Use labels in the same language as your text
- **Cost**: Same pricing regardless of language
- **Testing recommended**: Validate results for your specific language

---

## 🛡️ Security and Privacy

### Q: Is my data secure?
**A:**
- **Local Processing**: Data files stay on your computer
- **API Security**: Data transmitted securely to OpenAI (HTTPS)
- **No Storage**: OpenAI doesn't store your data (as per their policy)
- **API Key Security**: Keys stored in system keyring (encrypted)

### Q: Who can see my data?
**A:**
- **You**: Full control of your local data
- **OpenAI**: Processes data per their API terms (no storage/training use)
- **Nobody else**: Data isn't shared with third parties

### Q: Can I use CodebookAI for sensitive data?
**A:**
- **Consider carefully**: Review OpenAI's data usage policies
- **Anonymization**: Remove personally identifiable information when possible
- **Institutional policies**: Check your organization's data policies
- **Compliance**: Ensure compliance with GDPR, HIPAA, or other regulations if applicable

### Q: Where are my settings and results stored?
**A:**
- **Settings**: Stored locally in your user profile directory
- **API Keys**: Encrypted in system keyring
- **Results**: Saved wherever you choose when exporting
- **No cloud storage**: Everything stays on your computer unless you choose to share

---

## 🎯 Best Practices

### Q: How should I design my label set?
**A:**
1. **Be specific**: "positive_emotion" vs "positive"
2. **Avoid overlap**: Labels should be mutually exclusive (for single-label)
3. **Test small**: Validate with 10-20 examples before full processing
4. **Clear definitions**: Know exactly what each label means
5. **Reasonable number**: 3-10 labels work best; too many reduces accuracy

### Q: How do I prepare my text data?
**A:**
1. **Clean formatting**: Remove excess whitespace and formatting codes
2. **Consistent structure**: Same column layout across all files
3. **Reasonable length**: 50-500 words per text item optimal
4. **UTF-8 encoding**: Ensure proper character encoding
5. **Complete data**: Remove or handle missing/empty text

### Q: Should I use Live or Batch processing?
**A:** Choose based on:
- **Live Processing**: Testing, immediate results, <500 items, iterative development
- **Batch Processing**: Cost savings, large datasets (500+ items), non-urgent projects
- **Hybrid approach**: Test with Live, scale with Batch

### Q: How do I validate my results?
**A:**
1. **Manual sample review**: Check 50-100 random results
2. **Ground truth comparison**: Compare with known correct classifications
3. **Statistical analysis**: Use reliability statistics features
4. **Iterative improvement**: Refine labels based on results
5. **Documentation**: Keep notes on accuracy and issues found

---

## 🔗 Integration and Workflow

### Q: Can I export results to other tools?
**A:** Yes! CodebookAI exports to:
- **CSV files**: Compatible with Excel, R, Python, SPSS
- **Excel workbooks**: Multi-sheet files with statistics
- **Standard formats**: Easy import into most analysis tools

### Q: How do I integrate CodebookAI into my research workflow?
**A:** Typical workflow:
1. **Data preparation**: Clean and format your text data
2. **Label development**: Create clear, testable label sets
3. **Small-scale testing**: Use Live processing to validate approach
4. **Large-scale processing**: Use Batch processing for full dataset
5. **Quality validation**: Review results and calculate reliability
6. **Analysis**: Export to statistical software for further analysis

### Q: Can multiple people use CodebookAI on the same project?
**A:** Yes, but coordinate carefully:
- **Shared label sets**: Use identical labels across team members
- **Consistent settings**: Use same models and processing parameters
- **Data sharing**: Share results files for comparison and analysis
- **Version control**: Keep track of different processing runs

### Q: How do I cite CodebookAI in my research?
**A:** Suggested citation format:
```
CodebookAI [Version]. (2024). Retrieved from https://github.com/tmaier-kettering/CodebookAI

Text classification performed using OpenAI's [model name] via CodebookAI software.
```
Also cite the specific OpenAI model used and mention validation procedures.

---

## 🚨 Common Problems

### Q: Why is my import failing?
**A:** Most common causes:
1. **File format issues**: Ensure CSV/Excel is properly formatted
2. **Encoding problems**: Save as UTF-8 CSV
3. **File in use**: Close file in Excel before importing
4. **Large file size**: Split files larger than 100MB
5. **Missing headers**: Check "File has headers" setting

### Q: Why are my results inconsistent?
**A:** Possible causes:
1. **Ambiguous labels**: Labels too similar or unclear
2. **Model randomness**: AI responses have some natural variation
3. **Text quality**: Poor or inconsistent text quality
4. **Label definitions**: Unclear what each label should represent

### Q: My batch job seems stuck. What should I do?
**A:**
1. **Wait longer**: Batch jobs can take up to 48 hours
2. **Check OpenAI status**: Visit [status.openai.com](https://status.openai.com)
3. **Monitor dashboard**: Check job status in OpenAI dashboard
4. **Contact support**: Report stuck jobs to OpenAI if >48 hours

### Q: The interface looks broken or elements are missing.
**A:**
1. **Try maximizing**: Maximize the window
2. **Check display scaling**: Adjust system display settings
3. **Restart application**: Close and reopen CodebookAI
4. **Reset configuration**: Delete config file to reset interface

---

## 📈 Advanced Usage

### Q: Can I use custom prompts for classification?
**A:** Currently, CodebookAI uses optimized built-in prompts. Custom prompting is not available in the current version but may be added in future releases.

### Q: How do I handle very large datasets?
**A:**
1. **Split data**: Divide into smaller chunks (1000-5000 items each)
2. **Use batch processing**: Much more cost-effective for large datasets
3. **Progressive processing**: Process in stages, validate quality at each stage
4. **Memory management**: Ensure sufficient system RAM
5. **Time planning**: Allow adequate time for processing

### Q: Can I automate CodebookAI workflows?
**A:** The current version focuses on GUI workflows. Command-line automation may be added in future versions based on user demand.

### Q: How do I handle multi-language datasets?
**A:**
1. **Language consistency**: Keep text and labels in same language
2. **Model capabilities**: Test model performance on your specific language
3. **Cultural context**: Consider cultural factors in classification
4. **Validation**: Extra validation recommended for non-English languages

---

## 📞 Support and Community

### Q: Where can I get help if I'm stuck?
**A:**
1. **This FAQ**: Check for common questions and answers
2. **[Troubleshooting Guide](Troubleshooting.md)**: Detailed problem-solving steps
3. **[GitHub Issues](https://github.com/tmaier-kettering/CodebookAI/issues)**: Report bugs and get community help
4. **Documentation**: Comprehensive guides for all features

### Q: How do I report bugs or suggest features?
**A:**
1. **Search first**: Check if issue already reported
2. **GitHub Issues**: Use issue templates for bug reports
3. **Feature requests**: Describe use case and desired functionality
4. **Provide details**: Include system info, error messages, and steps to reproduce

### Q: Is CodebookAI actively maintained?
**A:** Yes! CodebookAI is actively developed and maintained. Check the [GitHub repository](https://github.com/tmaier-kettering/CodebookAI) for:
- Recent commits and updates
- Issue resolution activity
- Feature development progress
- Community discussions

### Q: Can I contribute to CodebookAI development?
**A:** Absolutely! Contributions are welcome:
- **Bug reports**: Help identify and fix issues
- **Feature suggestions**: Propose improvements
- **Documentation**: Help improve guides and examples
- **Code contributions**: Submit pull requests for bug fixes or features
- **Community support**: Help other users in discussions

---

## 🎓 Learning and Resources

### Q: Where can I learn more about text classification best practices?
**A:**
- **[Best Practices Guide](Best-Practices.md)**: CodebookAI-specific tips
- **Academic resources**: Research methods textbooks on content analysis
- **OpenAI documentation**: Learn about model capabilities and limitations
- **Community examples**: See how other researchers use CodebookAI

### Q: Are there example projects I can learn from?
**A:** Yes! Check out:
- **[Sample Workflows](Sample-Workflows.md)**: Complete project examples
- **[Use Cases](Use-Cases.md)**: Real-world applications
- **Sample datasets**: Included with CodebookAI installation
- **GitHub examples**: Community-contributed examples

### Q: How do I stay updated on new features?
**A:**
- **GitHub releases**: Subscribe to repository notifications
- **Documentation updates**: Check wiki for new guides
- **Community discussions**: Join GitHub discussions
- **Issue tracking**: Follow feature development

---

*Don't see your question here? Check the [Troubleshooting Guide](Troubleshooting.md) for detailed solutions or [ask on GitHub](https://github.com/tmaier-kettering/CodebookAI/issues/new) for community help!*