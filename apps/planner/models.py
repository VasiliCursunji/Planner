from datetime import datetime, timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from apps.planner.validators import WeekDayValidator


class BaseMixin(models.Model):
    class Meta:
        abstract = True

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class ProjectManager(BaseMixin):
    fullname = models.CharField(max_length=255, unique=True, verbose_name='PM Fullname')

    def __str__(self):
        return f'{self.__class__.__name__} - {self.fullname}'


class ProjectState(BaseMixin):
    name = models.CharField(max_length=255, unique=True, verbose_name='Project state')

    def __str__(self):
        return f'{self.__class__.__name__} - {self.name}'


class Project(BaseMixin):
    name = models.CharField(max_length=255, unique=True, verbose_name='Project Name')
    state = models.ForeignKey(ProjectState, on_delete=models.PROTECT, verbose_name='Project state')
    manager = models.ForeignKey(ProjectManager, on_delete=models.PROTECT, verbose_name='Project manager')

    def __str__(self):
        return f'{self.__class__.__name__} - {self.name}'


class Tech(BaseMixin):
    name = models.CharField(max_length=255, unique=True, verbose_name='Team tech')

    def __str__(self):
        return f'{self.__class__.__name__} - {self.name}'


class Team(BaseMixin):
    name = models.CharField(max_length=255, unique=True, verbose_name='Team name')
    tech = models.ForeignKey(Tech, on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.__class__.__name__} - {self.name}'


class TeamMember(BaseMixin):
    fullname = models.CharField(max_length=255, unique=True, verbose_name='Members fullname')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def get_timelog_for_current_week(self):
        d = datetime.now().date()
        current_week = d - timedelta(days=d.weekday())
        return TimeLog.objects.filter(member=self, week=current_week).aggregate(time=Sum('time'))['time']

    def __str__(self):
        return f'{self.__class__.__name__} - {self.fullname} ({self.team.name})'


class TimeLog(BaseMixin):
    class Meta:
        unique_together = [
            ['project', 'member', 'week']
        ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    week = models.DateField(validators=[WeekDayValidator([0])], verbose_name="Week")
    time = models.FloatField(validators=[MinValueValidator(0.0)])
    fact = models.FloatField(validators=[MinValueValidator(0.0)], null=True, default=float(0))

    def __str__(self):
        return f'{self.__class__.__name__} - {self.project.name} ({self.time} h)'


class TimePlan(BaseMixin):
    class Meta:
        unique_together = [
            ['project', 'tech', 'week']
        ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tech = models.ForeignKey(Tech, on_delete=models.PROTECT, verbose_name='Team Tech')
    week = models.DateField(validators=[WeekDayValidator([0])], verbose_name="Week")
    time = models.FloatField(validators=[MinValueValidator(0.0)])

    def __str__(self):
        return f'{self.__class__.__name__} - {self.project.name} ({self.time} h)'


class TimePlanSummary(TimePlan):
    class Meta:
        proxy = True
        verbose_name = 'Time Plan Summary'
        verbose_name_plural = 'Time Plan Summaries'

    def get_back_end(self):
        return TimePlan.objects.filter(
            project=self.project,
            week=self.week,
            tech__name='Back-end'
        ).aggregate(time=Sum('time'))['time']

    def get_front_end(self):
        return TimePlan.objects.filter(
            project=self.project,
            week=self.week,
            tech__name='Front-end'
        ).aggregate(time=Sum('time'))['time']

    def get_mobile(self):
        return TimePlan.objects.filter(
            project=self.project,
            week=self.week,
            tech__name='Mobile'
        ).aggregate(time=Sum('time'))['time']

    def get_analiza(self):
        return TimePlan.objects.filter(
            project=self.project,
            week=self.week,
            tech__name='Analiza'
        ).aggregate(time=Sum('time'))['time']

    def get_time_logged(self):
        return TimeLog.objects.filter(
            week=self.week,
            project=self.project
        ).aggregate(time=Sum('time'))['time']

    def get_time_planned(self):
        return TimePlan.objects.filter(
            week=self.week,
            project=self.project
        ).aggregate(time=Sum('time'))['time']

    def get_in_fact(self):
        return TimeLog.objects.filter(
            week=self.week,
            project=self.project
        ).aggregate(fact=Sum('fact'))['fact']

    def get_difference(self):
        logged = self.get_time_logged()
        planned = self.get_time_planned()
        if not logged:
            logged = 0
        if not planned:
            planned = 0
        return planned - logged


class TimeLogSummary(TimeLog):
    class Meta:
        proxy = True
        verbose_name = 'Time Log Summary'
        verbose_name_plural = 'Time Log Summaries'

    def get_members(self):
        logs = TimeLog.objects.filter(
            week=self.week,
            member__team=self.member.team
        )
        result = ''
        for i in logs:
            result += '<p>{}({}) - {}h</p>'.format(
                i.member.fullname,
                i.project.name,
                i.time
            )

        return result

    def get_projects(self):
        projects = TimeLog.objects.filter(
            week=self.week,
            member__team=self.member.team,
        ).order_by('project').distinct('project')

        result = ''
        for i in projects:
            result += '<p style={}>{}</p>'.format(
                'font-style:italic',
                i.project.name,
            )

        return result

    def get_time_logged(self):
        return TimeLog.objects.filter(
            week=self.week,
            member__team=self.member.team
        ).aggregate(time=Sum('time'))['time']

    def get_time_planned(self):
        return TimePlan.objects.filter(
            week=self.week,
            tech__team=self.member.team
        ).aggregate(time=Sum('time'))['time']

    def get_team_work(self):
        return TimeLog.objects.filter(
            week=self.week,
            member__team=self.member.team
        ).aggregate(fact=Sum('fact'))['fact']

    def get_difference(self):
        logged = self.get_time_logged()
        planned = self.get_time_planned()
        if not logged:
            logged = 0
        if not planned:
            planned = 0
        return planned - logged
