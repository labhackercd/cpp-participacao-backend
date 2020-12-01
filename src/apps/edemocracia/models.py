from utils.model_mixins import AnalysisMixin


class EdemocraciaAnalysis(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')


class EdemocraciaGA(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')
