from utils.model_mixins import AnalysisMixin


class PautasGA(AnalysisMixin):
    pass

    class Meta:
        unique_together = ('start_date', 'period')
